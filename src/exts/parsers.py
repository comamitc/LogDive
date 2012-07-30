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
import re, time
import lxml.etree as tree
from collections import namedtuple
from lxml import _elementpath as _dummy

FORMATS = ("%Y-%m-%d %H:%M:%S"   ,      #.log
           "%Y%m%d_%H.%M.%S"     ,      #.xml
           "%a %b %d %H:%M:%S %Y")      #.txt


''' namedtuple instance of Line() class for lighter objects '''
Line = namedtuple('Line', 'filename,time,ftime,lvl,msg')


#Two Methods for parsing and transforming time... no need for object overhead
def decode(fn, t, lvl, msg):
    """ decode 'line' to a Line Object """
    ext = fn[-4:]
    try:       
        if ext == '.log':
            t = _hacktime(t, FORMATS[0])
        elif ext == '.xml':
            t = _hacktime(t, FORMATS[1])
        elif ext == '.txt':
            t = _hacktime(' '.join([t, time.strftime('%Y')]), FORMATS[2])
        else:
            raise Exception("No parsing handler for file: {0!r}".format(fn))
    except ValueError:
        print ValueError("Error parsing time value: {0!r}".format(t))
        t = (time.time(), time.ctime(time.time()))
    return Line(fn, t[0], t[1], lvl, msg)

def _hacktime(t, format):
    """ hack meant for time object recognition to aid in sorting 
        return list [milliseconds, string formatted time]"""
    t = time.mktime(time.strptime(t, format))    
    return (t, time.ctime(t))

class TextParser(object):
    
    _tsa = re.compile(r'^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}.*$')                    #19
    _tsb = re.compile(r'^\[?[a-zA-Z]{3}\s[a-zA-Z]{3}\s\d{2}[ T]\d{2}:\d{2}:\d{2}.*$')   #20
    _store = []

    def parse_text(self, file, ts):
        self.file = file
        self.timestamp = ts
        with open(file, 'r') as f:
            self._sift(f.readlines(), ts)
        return self._store

    def _split(self, c, i, ts):
        j, k = 0, 1
        s = len(i)
        while k < s:
            e, f = i[j], i[k]
            _tmp = "".join(c[e:f]).lower()
            lvl = 'INFO'
            if 'error' in _tmp or 'exception' in _tmp:
                lvl = 'ERROR'
                nl = decode(self.file, _tmp[:19], 
                            lvl,       _tmp[20:])
                if ts < nl.time:
                    self._store.append(nl)
            j, k = k, k + 1
    
    def _sift(self, contents, ts):
        i = 0
        _idxs = []
        for line in contents:
            if self._tsb.match(line) or self._tsa.match(line):    
                _idxs.append(i)
            i += 1
        if len(_idxs) > 1:
            self._split(contents, _idxs, ts)


class XMLParser(object):
    
    _store = []
    
    def parse_xml(self, file, ts): 
        #try should catch malformed XML
        try:     
            ctx = tree.iterparse(file, tag='LINE')
            for evt, elm in ctx:
                nl = decode(file,        elm[0].text, 
                            elm[1].text, elm[3].text)
                if nl.lvl == 'ERROR' and ts < nl.time:
                    self._store.append(nl)
                while elm.getprevious() is not None:
                    del elm.getparent()[0]
            del ctx
        except Exception as error:
            print("Error parsing %s because %s. Skipping..." % (file, error))
            return #exit XML parse iteration and resume at next file
        #if all was successful
        return self._store
    
    
    
    