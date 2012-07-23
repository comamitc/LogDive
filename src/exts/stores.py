"""
Copyright (c) 2012 Mitchell Comardo

Permission is hereby granted, free of charge, to any person obtaining a copy of 
this software and associated documentation files (the "Software"), to deal in 
the Software without restriction, including without limitation the rights to use, 
copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the 
Software, and to permit persons to whom the Software is furnished to do so, subject 
to the following conditions:

    The above copyright notice and this permission notice shall be included in 
    all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A 
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT 
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION 
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE 
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
import os, time, shutil, csv, json, threading
import cPickle as pickle

exists = os.path.exists


# ToDo: Implement this as namedtuple
class Line(dict):
    """ Line _subset_(dict) class.  Creates an instance of Line Object that 
        includes to help with comparisons when sorting and filtering
    """
    def __init__(self, filename, milliseconds, 
                 formattime, level, message,
                 *args, **kwargs):
        #subclass fo Dict
        dict.__init__(self, *args, **kwargs)
        #this object's attributes
        self['filename'] = filename
        self['ms'] = milliseconds
        self['formattime'] = formattime
        self['lvl'] = level
        self['msg'] = message

        def __str__(self):
            """ string representation of Line class
            """
            _args = []
            for k, v in self.items():
                _args.insert(0, v)
            return "\n".join(_args) + '\n'

class Codex(object):
    """The Codex Class helps decode plain text or XML attributes to a Line Object
    (acting as a Factory for Lines) and provides a nice clean hack for the Time
    Objects in PPSS Log Files
    """
    #given time formats for PPSS logs
    FORMATS = ["%Y-%m-%d %H:%M:%S"      , #.log
               "%Y%m%d_%H.%M.%S"        , #.xml
               "%a %b %d %H:%M:%S %Y"]    #.txt
        
    def decode(self, fn, t, lvl, msg):
        """ decode 'line' to a Line Object """
        t = self._hacktime(t, fn[-4:])
        return Line(fn, t[0], t[1], lvl, msg)

    def _hacktime(self, t, ext):
        """ hack meant for time object recognition to aid in sorting 
            return list [milliseconds, string formatted time]"""
        try:       
            if ext == '.log':
                t = time.mktime(time.strptime(t, self.FORMATS[0]))
            elif ext == '.xml':
                t = time.mktime(time.strptime(t, self.FORMATS[1]))
            elif ext == '.txt':
                t = time.mktime(time.strptime(' '.join([t, 
                                                        time.strftime('%Y')]),
                                                        self.FORMATS[2]))
            
        except ValueError:
            print ValueError("Error parsing time value: {0!r}".format(t))
            t = time.time()
        return [t, time.ctime(t)]


class LogStore(object):
    """LogStore Object manufactures the LogAnalysis Summary file by collecting 
    lines of interest (explicitly stored lines) and allows for dumping of the 
    values into a summary file
    """
    _ERRC = 1
    _FILES = {}
    
    def __init__(self, filename):
        self._data = []
        self.logfile = filename
        self._lfile = None
        self._lock = threading.Lock()
        self.Codec = Codex()
    
    #should depreciate slowly
    def put(self, obj, key=None):
        """ Puts a Line object into the Repo while recording Error Count and
        last filename to assemble the summary's header"""
        if isinstance(obj, Line):
            if obj['filename'] != self._lfile and self._lfile != None:
                self._FILES[obj['filename']] = self._ERRC
                self._ERRC = 1
            else:
                self._data.append(obj)
                self._ERRC += 1
            self._lfile = obj['filename']
        else:
            raise ValueError("Something went horribly wrong in appending..")
        
    def put_many(self, obj, key=None):
        """ Merges an additional list with the current one to clean up the store interface"""
        raise NotImplementedError
    
    def _assemble(self):
        """ private method used to assemble summary header"""
        summary = []
        LBS = '#'
        summary.append("LogDive Finished Analysis\n\n")
        summary.append("%s" %(LBS*128))
        for k, v in self._FILES.items():
            summary.append("%s||%s" % (k.ljust(116), 
                                       str(v).rjust(10)))
        else:
            summary.append("No more log files were updated since last runtime.")
        summary.append("%s\n\n\n" % (LBS*128))
        return "\n".join(summary)
    
    def close(self):
        """ close store a.k.a. assemble header, write updated lines to new summary
        file"""
        header = self._assemble()
        _data = sorted(self._data, key=lambda x: x['ms'])
        # I dont like this because it's a bit complicated
        _data = '\n\n'.join(['\n'.join([str(y) for y in reversed(x.values())]) for x in _data])
        data = header + _data
        
        with open(self.logfile, 'w') as f:
            self._lock.acquire()
            f.write(data)
            self._lock.release()
    
    #ToDo: Implement sync mechanism for the text file (tmp file?) // could be handled by exit function
    def sync(self):
        # how to sync and sort?
        raise NotImplementedError
        '''tmp = self.logfile + '.tmp'
        with open(tmp, 'a') as tmpf:
            pass'''
    
# ToDo: Implement this as namedtuple
class ObjectStore(dict):
    ''' 
    Persistent dictionary with an API compatible with shelve and anydbm.

    The dict is kept in memory, so the dictionary operations run as fast as
    a regular dictionary.

    Write to disk is delayed until close or sync (similar to gdbm's fast mode).

    Input file format is automatically discovered.
    Output file format is selectable between pickle, json, and csv.
    All three serialization formats are backed by fast C implementations.
    '''
    def __init__(self, filename, flag='c', mode=None, format='pickle', *args, **kwds):
        self.flag = flag                    # r=readonly, c=create, or n=new
        self.mode = mode                    # None or an octal triple like 0644
        self.format = format                # 'csv', 'json', or 'pickle'
        self.filename = filename
        if flag != 'n' and os.access(filename, os.R_OK):
            fileobj = open(filename, 'rb' if format=='pickle' else 'r')
            with fileobj:
                self.load(fileobj)
        dict.__init__(self, *args, **kwds)

    def sync(self):
        'Write dict to disk'
        if self.flag == 'r':
            return
        filename = self.filename
        tempname = filename + '.tmp'
        fileobj = open(tempname, 'wb' if self.format=='pickle' else 'w')
        try:
            self.dump(fileobj)
        except Exception:
            os.remove(tempname)
            raise
        finally:
            fileobj.close()
        shutil.move(tempname, self.filename)    # atomic commit
        if self.mode is not None:
            os.chmod(self.filename, self.mode)

    def close(self):
        self.sync()

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.close()

    def dump(self, fileobj):
        if self.format == 'csv':
            csv.writer(fileobj).writerows(self.items())
        elif self.format == 'json':
            json.dump(self, fileobj, separators=(',', ':'))
        elif self.format == 'pickle':
            pickle.dump(dict(self), fileobj, 2)
        else:
            raise NotImplementedError('Unknown format: ' + repr(self.format))

    def load(self, fileobj):
        # try formats from most restrictive to least restrictive
        for loader in (pickle.load, json.load, csv.reader):
            fileobj.seek(0)
            try:
                return self.update(loader(fileobj))
            except Exception:
                pass
        raise ValueError('File not in a supported format')