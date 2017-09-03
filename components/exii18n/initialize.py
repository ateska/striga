#!/usr/bin/env python

# This script should be use to initialize babel locale data

import sys, os

os.chdir(os.path.dirname(__file__))

os.system('cd babel-0.9.5 && scripts/import_cldr.py ../cldr-1.6.1-core')
