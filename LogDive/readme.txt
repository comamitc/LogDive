Copyright (c) 2012 Mitchell Comardo

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


############################################################################

	LogDive

############################################################################


CAUTION:  Please don't use this as your sole source of debugging with PPSS.  This tool can be useful 
with debugging and expedite the debugging process in the case that the log files are definitive in their 
explanation. 


Version		: 1.0.7
Author 		: Mitchell Comardo
Report Bugs To	: comamitc@gmail.com


CHANGELOG:

	1.0.7:
		- debug configuration switch
		- archive old ppss log files to reduce scan times
		
	1.0.0:
		- Complete application rewritten with OO design.  Built to be extensible and supply filters which will be 
		a future feature
		- striped out email bulk as not secure on servers.

	0.7.5:
		- fast_parse algorithm for xml processing (down to 9 seconds per 300MB file, pure text remains very fast)
	0.7.2:
		- Fixed Logging of old files
	0.7.1:
		- History Log improvement; should provide better scans
	0.7.0:
		- Log History
	0.6.0:
		- Log summary sorting
		- i/o optimization (60% increase)
	0.5.0:
		- added log file clean-up and bundled scripts
		- fixed import related issues
	0.4.5:
		- Added file summary & further optimizations
	0.4.1:
		- general optimization and refractoring
	0.4.0:
		- introduction of logmail: an email task to attach summary
	0.3.6:
		- optional debugging
	0.3.5: 
		- corrected 'history' bug
	0.3.2:
		- xml parsing speed-up
	0.3.1:
		- Added 'history' capture to minimize the amount of rescanning
	0.2.9:
		- Added XML and PLAINTEXT objects to expedite processing
		- Cleaner formatted logs

INSTALLATION:
	
	Dependencies:
		- Windows XP or greater
		- UNIX not supported
		- PPSS installation or PPSS generated logs

	Steps:
		1.) UnZip structure
		2.) Navigate to 'config/config.ini' 
			- Change PPSS_DIR to the base level PPSS installation folder
				o This can be comma separated without spaces if you have a multi-host environment
		3.) Doubleclick the LogDive executable or run from command line for more stable debugging information.
		4.) Log files will be generated and stored in the logs directory

	 