import os, time

VersionFilename = os.path.join(os.path.dirname(__file__), 'version.txt')
Version = file(VersionFilename, 'r').read().replace('($','').replace('$)','').strip()
