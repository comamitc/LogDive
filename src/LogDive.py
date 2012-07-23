#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
import os, time
import ConfigParser
import zipfile
import cProfile as prof
from exts.parsers import TextParser, XMLParser
from exts.stores import ObjectStore, LogStore

class LogDive(object):
    
    LOG_DIR = 'build/log'                                           #logs in PPSS Directory
    DAT_FILE = 'logs/LogAnalysis%s.log' % int(time.time())          #database file
    HIST_FILE = 'data/history.dat'                                  #do I need this?
    
    def __init__(self, cfg, abs_path):
        """ Initializes LogDive configuration, Parsers, History recording
        and Summary writer
        """
        _dirs = cfg.get('general', 'ppss_dirs').split(',')
        self.dirs = map(lambda x: '/'.join([x, self.LOG_DIR]), _dirs)
        self._arch = cfg.getboolean('general', 'archive')
        self.store = LogStore('/'.join([abs_path, self.DAT_FILE]))
        self.history = ObjectStore('/'.join([abs_path, self.HIST_FILE]))
        self.texter = TextParser(self.store)
        self.xster = XMLParser(self.store)
        self._archs = [] #dirty implementation for archiving

    def archive(self):
        """ archive the old log files if mode is turned on"""
        if self._arch:
            print("archiving...")
            ldir = None
            zf = None
            for ea in self._archs:
                #have we already scanned this file in this directory?
                if ea[0] != ldir:
                    if zf is not None: zf.close()
                    ldir = ea[0]
                    zf = zipfile.ZipFile('\\'.join([ea[0],'archive.zip']), 'a')
                zf.write(ea[1], ea[2])
                os.remove(ea[1])
            if zf is not None: zf.close()
            #print("Done archiving")

    def _get_lines(self, ff, ts):
        """ generic abstraction for triggering the right type if 
        parser based on a File's ext"""
        _funcs = {'.xml': self.xster.parse_xml,
                  '.txt': self.texter.parse_text,
                  '.log': self.texter.parse_text}
        f_ext = ff[-4:]
        if _funcs.has_key(f_ext):
            func = _funcs[f_ext]
            func(ff, ts)
            self.history[ff] = {'last': time.time()}
    
    #TODO:
    # - add encoding for umlauts in logs
    def parse_logs(self):
        """ Function pages through given directories in config file
        then files in each directory, firing parsing based on 
        files modified at time and historical scan time."""
        for dir in self.dirs:
            for f in os.listdir(dir):
                ff = '/'.join([dir, f])
                ffmod = int(os.stat(ff)[8])
                start = time.time()
                if self.history.has_key(ff):
                    fflast = self.history[ff]['last']
                    if ffmod > fflast:
                        self._get_lines(ff, fflast)
                    elif ffmod < (time.time() - 432000):                            
                        #zip archiving :: file unmodified for 5 days
                        self._archs.append([dir, ff, f])
                else: 
                    self._get_lines(ff, float(0))
                end = time.time()
                print("%s :: %s ms" % ((ff.split('/')[-1]).ljust(56), 
                                        str(end-start)[:10].rjust(15)))
                # sync after each file
                self.history.sync()
        # sync summary
        self.store.close()
        
        
if __name__ == "__main__":
    #    SCRIPT ENTRY
    #    CONFIGURATION SECTION BELOW
    #
    INIFILE = 'config/config.ini'
    
    abs_path = os.path.realpath('.')
    
    cfg = ConfigParser.ConfigParser()
    cfg.read('%s' % '/'.join([abs_path, INIFILE]))
    
    #    Start parsing process
    print("starting analysis:")
    diver = LogDive(cfg, abs_path)
    if cfg.getboolean('general', 'debug'):
        prof.run('diver.parse_logs()')
    else:
        diver.parse_logs()
    print("finished scanning :: Analysis in %s" % '\\'.join([abs_path, 'logs']))
    
    #I don't like this implementation
    diver.archive()
    
    print("DONE")
    
