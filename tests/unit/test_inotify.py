#!/usr/bin/env python

import pytest
from butter.inotify import watch

from subprocess import Popen
from tempfile import TemporaryDirectory
from time import sleep
import os

def test_watch():
    FILENAME = 'inotify_test'
    with TemporaryDirectory() as tmp_dir:
        filename = os.path.join(tmp_dir, FILENAME)
        
        proc = Popen('sleep 0.04 ; touch {}'.format(filename), shell=True)
        
        event = watch(tmp_dir)
        
        proc.wait()
