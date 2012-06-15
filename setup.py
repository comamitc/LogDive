from distutils.core import setup
import py2exe, sys

sys.path.append('C:\\DEV\\PY\\LogDive\\src\\')

includes = ['exts.parsers', 'exts.stores']

setup(name='LogDive',
      author='Mitch Comardo',
      version='1.0.7',
      console=['src/LogDive.py'],
      options={ 'py2exe':
                {
                'dist_dir'      :   'LogDive', 
                'packages'      :   ['gzip'],
                'optimize'      :   2,
                'bundle_files'  :   1,
                'includes'      :   includes
                }},
      zipfile=None,
      data_files=[
                  ("config", ["src/config/config.ini"])
                 ]
      )
