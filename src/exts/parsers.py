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
import re
import lxml.etree as tree
from lxml import _elementpath as _dummy

class TextParser(object):
    
    _tsa = re.compile(r'^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}.*$')                    #19
    _tsb = re.compile(r'^\[?[a-zA-Z]{3}\s[a-zA-Z]{3}\s\d{2}[ T]\d{2}:\d{2}:\d{2}.*$')   #20

    def __init__(self, Store):
        self._store = Store

    def parse_text(self, file, ts):
        self.file = file
        self.timestamp = ts
        with open(file, 'r') as f:
            self._sift(f.readlines(), ts)

    def _split(self, c, i, ts):
        j, k = 0, 1
        s = len(i)
        while k < s:
            e, f = i[j], i[k]
            _tmp = "".join(c[e:f])
            lvl = 'INFO'
            if 'error' in _tmp.lower() or 'exception' in _tmp.lower():
                lvl = 'ERROR'
                nl = self._store.Codec.decode(self.file, 
                                             _tmp[:19], 
                                             lvl,
                                             _tmp[20:])
                if ts < nl['ms']:
                    self._store.put(nl)
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
    
    def __init__(self, Store):
        self._store = Store
    
    def parse_xml(self, file, ts): 
        #try should catch malformed XML
        try:     
            ctx = tree.iterparse(file, tag='LINE')
            for evt, elm in ctx:
                nl = self._store.Codec.decode(file, 
                                         elm[0].text, 
                                         elm[1].text,
                                         elm[3].text)
                if nl['lvl'].lower() == 'error' and ts < nl['ms'] :
                    self._store.put(nl)
                while elm.getprevious() is not None:
                    del elm.getparent()[0]
            del ctx
        except Exception as error:
            print("Error parsing %s because %s. Skipping..." % (file, error))
            return #exit XML parse iteration and resume at next file
        
    
    
    
    