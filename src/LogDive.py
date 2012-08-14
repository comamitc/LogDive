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
from exts.parsers import TextParser, XMLParser
from exts.stores import ObjectStore, LogStore

#ToDo: turn file into a named tuple implementation

class LogDive(object):
    
    LOG_DIR = 'build/log'                                           #logs in PPSS Directory
    DAT_FILE = 'logs/LogAnalysis%s.log' % int(time.time())          #database file
    HIST_FILE = 'data/history.dat'                                  #data file for scan tracking
    ARCH_LIM = (5 * 24 * 60 * 60)                                   #5 day threshold for archiving
        
    def __init__(self, abs_path, log_dirs, archive=False):
        """ Initializes LogDive configuration, Parsers, History recording
        and summary writer
        """    
        _dirs = log_dirs.split(',')
        self.dirs = map(lambda x: '/'.join([x, self.LOG_DIR]), _dirs)
        self._arch = archive
        self.store = LogStore('/'.join([abs_path, self.DAT_FILE]))
        self.history = ObjectStore('/'.join([abs_path, self.HIST_FILE]))
        self.texter = TextParser()
        self.xster = XMLParser()

    def archive(self, dir, fullpath, file):
        """ archive the old log files if mode is turned on"""
        zf = zipfile.ZipFile('\\'.join([dir,'archive.zip']), 'a')
        zf.write(fullpath, file)
        os.remove(fullpath)
        zf.close()

    def _get_lines(self, ff, ts):
        """ generic abstraction for triggering the right type if 
        parser based on a File's ext"""
        _funcs = {'.xml': self.xster.parse_xml,
                  '.txt': self.texter.parse_text,
                  '.log': self.texter.parse_text}
        f_ext = ff[-4:]
        if _funcs.has_key(f_ext):
            func = _funcs[f_ext]
            _data = func(ff, ts)
            self.store.put_many(ff, _data)
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
                if self.history.has_key(ff): #old file that has be scanned
                    fflast = self.history[ff]['last']
                    if ffmod > fflast: #has file been modified?
                        self._get_lines(ff, fflast)
                    elif ffmod < (time.time() - self.ARCH_LIM) and self._arch: #is file ready for archiving  
                        self.archive(dir, ff, f)
                else: #new file that has never be scanned
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
    diver = LogDive(abs_path, 
                    cfg.get('general', 'ppss_dirs'), 
                    cfg.getboolean('general', 'archive'))
    if cfg.getboolean('general', 'debug'):
        import cProfile as prof
        import pstats
        prof.run('diver.parse_logs()', 'run.log')
        p = pstats.Stats('run.log')
        p.sort_stats('time')
        p.print_stats()
    else:
        diver.parse_logs()
    
    print("Done!")
    
