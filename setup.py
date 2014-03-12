#!/usr/bin/env python

import sys

name = 'butter'
path = 'butter'

## Automatically determine project version ##
from setuptools import setup, find_packages
try:
    from hgdistver import get_version
except ImportError:
    def get_version():
        import os
        
        d = {'__name__':name}

        # handle single file modules
        if os.path.isdir(path):
            module_path = os.path.join(path, '__init__.py')
        else:
            module_path = path
                                                
        with open(module_path) as f:
            try:
                exec(f.read(), None, d)
            except:
                pass

        return d.get("__version__", 0.1)

## Use py.test for "setup.py test" command ##
from setuptools.command.test import test as TestCommand
class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True
    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        pytest.main(self.test_args)

## Try and extract a long description ##
for readme_name in ("README", "README.rst", "README.md"):
    try:
        readme = open(readme_name).read()
    except (OSError, IOError):
        continue
    else:
        break
else:
    readme = ""

## Finally call setup ##
setup(
    name = name,
    version = get_version(),
    packages = [path], # corresponds to a dir 'epicworld' with a __init__.py in it
    author = "Da_Blitz",
    author_email = "code@pocketnix.org",
    maintainer=None,
    maintainer_email=None,
    description = "Library to interface to low level linux features",
    long_description = readme,
    license = "MIT BSD",
    keywords = "linux splice tee fanotify inotify clone unshare",
    download_url = "http://code.pocketnix.org/butter/archive/tip.tar.bz2",
#    classifiers = ["Programming Language :: Python :: 3",],
    platforms=None,
    url = "http://code.pocketnix.org/butter/file/tip",
#    entry_points = {"console_scripts":["hammerhead=hammerhead:main",
#                                       "hammerhead-enter=hammerhead:setns"],
#                   },
#    scripts = ['scripts/dosomthing'],
    zip_safe = False,
    setup_requires = [],
    install_requires = ['distribute', 'cffi>=0.7.2'],
    tests_require = ['tox', 'pytest', 'pytest-cov'],
    cmdclass = {'test': PyTest},
    ext_package = name,
)
