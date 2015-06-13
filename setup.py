#!/usr/bin/env python

from butter import clone, _eventfd, _fanotify, _inotify, seccomp
from butter import _signalfd, splice, system, _timerfd, utils


name = 'butter'
path = 'butter'

## Automatically determine project version ##
from setuptools import setup
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
readme = ""
for readme_name in ("README", "README.rst", "README.md",
                    "CHANGELOG", "CHANGELOG.rst", "CHANGELOG.md"):
    try:
        readme += open(readme_name).read() + "\n\n"
    except (OSError, IOError):
        continue

## Finally call setup ##
setup(
    name = name,
    version = get_version(),
    packages = [path, path + "/asyncio"],
    author = "Da_Blitz",
    author_email = "code@pocketnix.org",
    maintainer=None,
    maintainer_email=None,
    description = "Library to interface to low level linux features (inotify, fanotify, timerfd, signalfd, eventfd, containers) with asyncio support",
    long_description = readme,
    license = "MIT BSD",
    keywords = "linux splice tee fanotify inotify eventfd signalfd timerfd aio clone unshare asyncio container server async",
    download_url = "http://blitz.works/butter/archive/tip.tar.bz2",
    classifiers = [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Systems Administration",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Developers",
        ],
    platforms=None,
    url = "http://blitz.works/butter/file/tip",
#    entry_points = {"console_scripts":["hammerhead=hammerhead:main",
#                                       "hammerhead-enter=hammerhead:setns"],
#                   },
#    scripts = ['scripts/dosomthing'],
    zip_safe = False,
    ext_package = name,
    ext_modules = [
        clone.ffi.verifier.get_extension(),
        _eventfd.ffi.verifier.get_extension(),
        _fanotify.ffi.verifier.get_extension(),
        _inotify.ffi.verifier.get_extension(),
        seccomp._ffi.verifier.get_extension(),
        _signalfd.ffi.verifier.get_extension(),
        splice._ffi.verifier.get_extension(),
        system._ffi.verifier.get_extension(),
        _timerfd.ffi.verifier.get_extension(),
        utils._ffi.verifier.get_extension(),
        ],
    setup_requires = [],
    install_requires = ['cffi>=0.7.2'],
    tests_require = ['tox', 'pytest', 'pytest-cov', 'pytest-mock', 'mock'],
    cmdclass = {'test': PyTest},
)
