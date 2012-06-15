'''
Created on Jan 12, 2012

@author: mfrank

Extensions for LogDive
'''
import re, os
import cPickle
import time

FORMATS = ["%Y-%m-%d %H:%M:%S",
           "%Y%m%d_%H.%M.%S",
           "%a %b %d %H:%M:%S %Y"] #Wed Jan 11 13:17:23

class XmlLine(object):
    
    def __init__(self, elm):
        
        #fastest way to get children and store
        self.time = elm[0].text
        self.level = elm[1].text
        self.msg = elm[3].text
        
    
class PlainLine(object):
    
    def __init__(self, line):
        self.time = line[:19]
        self.msg = line[20:].lower()
           

class TextFile(object):
    
    _tsa = re.compile(r'^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}.*$') #19
    _tsb = re.compile(r'^\[?[a-zA-Z]{3}\s[a-zA-Z]{3}\s\d{2}[ T]\d{2}:\d{2}:\d{2}.*$') #20
    
    def __init__(self, contents):
        self._idxs = []
        self.lines = self._sift(contents)
        
    def _split(self, contents):
        _new_lines = []
        j, k = 0, 1
        while k < len(self._idxs):
            e, f = self._idxs[j], self._idxs[k]
            _new_lines.append(PlainLine(''.join(contents[e:f])))
            j, k = k, k + 1
        return _new_lines
        
    def _sift(self, contents):
        '''
            PPSS logs are unique in they you are able to distinguish lines
            based on dates that for the beginning 19-20 characters in a line
        '''
        i = 0
        #regex match date string signifying new lines
        for line in contents:
            if self._tsb.match(line) or self._tsa.match(line):    
                self._idxs.append(i)
            i += 1
        #if there appear to be lines _split the contents
        return self._split(contents) if len(self._idxs) > 1 else None
        

class CustomLog(object):
    
    _errcount = 0
    _ttle = 0
    _ttlf = 0
    _files = {}
    
    def __init__(self, path, history):
        self.__p = path
        self._lines =   []
        #this needs to be cleaner!!!
        #initailize history
        self._time_token =  history._data['last_t']  
        del history                 
    
    def write(self, fname, t, msg):
        
        # try to create a timestamp from T
        # in the case that none of these stamps work -> 
        # create a dumby time
        try:
            t = time.mktime(time.strptime(t, FORMATS[0]))
        except:
            try:
                t = time.mktime(time.strptime(t, FORMATS[1]))
            except:
                try:
                    t = time.mktime(time.strptime(' '.join([t, 
                                                    time.strftime('%Y')]),
                                                    FORMATS[2]))
                except Exception as e:
                    print('could not convert time %s: %s' % (t, e))
                    t = float(0)
        
        #test if this line is new or old!
        new_line = [fname, t, msg]
        if t < self._time_token:
            return False
        self._lines.append(new_line)
        self._errcount += 1
        self._ttle += 1
        
        
    def eof(self, fname):
        ''' insert a line break after processing a file '''
        self._ttlf += 1
        self._files[fname] = self._errcount
        self._errcount = 0 #reintialize for next file
    
    def _summary(self):
        summary = []
        LBS = '#'
        summary.append('LOG ANALYSIS COMPLETED\n\n%s' % (LBS*100))
        for k,v in self._files.items():
            summary.append("%s||%s" % (k.ljust(78), 
                                       str(v).rjust(20)))
        summary.append('%s' % (LBS*100))
        return '\n'.join(summary)
     
    def _tconvert(self, lines):
        for line in lines:
            line[1] = time.ctime(line[1])
        return lines
        
    def close(self):
        '''
            create summary lines _summary()
            copy self._lines to not change them for history
            convert time to string from EPOCH float
            join all the err_lines together
            join the summary to err_lines to create log file
            write that file
        '''
        sum_lines = self._summary()
        err_lines = self._tconvert(sorted(self._lines, key=lambda x: x[1]))
        err_lines = '\n\n'.join(['\n'.join(x) for x in err_lines])
        new_lines = '\n\n'.join([sum_lines, err_lines])
        f = open(self.__p, 'w')
        f.write(new_lines)
        f.close()
        
class HistoryLog(object):
    '''
        HistoryLog provides historically scanned logs
        
        this class lets us skip files that have been scanned already
        and expedite the scanning process
    '''
    def __init__(self, path):
        self._file = path
        self._data = {}
        #check for file existing
        if not os.path.isfile(self._file):
            self._data['last_t'] = 0
        else:
            self._data = self._load()
    
    def _load(self):
        '''
            load the history.dat object from files
        '''
        return cPickle.load(open(self._file, 'r'))
    
    def update(self, key, value):
        self._data[key] = value
    
    def save(self, last_run=0):
        #save historical lines
        #for calling back
        self._data['last_t'] = last_run
        cPickle.dump(self._data, open(self._file, 'w'))
    
    def get(self, key):
        return self._data[key]
     
    def has_key(self, key):
        return self._data.has_key(key)


        
        
  
        
        