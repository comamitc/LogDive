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
import os, shutil, csv, json, threading
import cPickle as pickle

exists = os.path.exists #simplify this call


class LogStore(object):
    """LogStore Object manufactures the LogAnalysis Summary file by collecting 
    lines of interest (explicitly stored lines) and allows for dumping of the 
    values into a summary file
    """
    _ERRC = 1
    _FILES = {}
    _lock = threading.Lock()
    
    def __init__(self, filename):
        self._data = []
        self.logfile = filename
        self._lfile = None
    
    def put_many(self, filename, obj, key=None):
        """ Merges an additional list with the current one to clean up the store interface"""
        self._FILES[filename] = len(obj)
        self._data.extend(obj)
        
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
        _data = sorted(self._data, key=lambda x: x.time)
        # I dont like this because it's a bit complicated
        _data = '\n\n'.join(['\n'.join([str(y) for y in x.__getnewargs__()]) for x in _data])
        data = header + _data
        
        with open(self.logfile, 'w') as f:
            self._lock.acquire()
            f.write(data)
            self._lock.release()
        
    
    def __exit__(self, *exc_info):
        self.close()


    
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