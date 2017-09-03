#!/usr/bin/env strigapython

import os, sys, optparse, fnmatch

###

def _unlink(root, fname):
	fullfname = os.path.join(root,fname)
	print ">R", fullfname
	os.unlink(fullfname)
	
def cmd_clean(options):
	print "Cleaning ..."

	for root, dirs, files in os.walk(os.getcwd()):
		for fname in files:
			if fnmatch.fnmatch(fname, "*.pyc"):
				_unlink(root, fname)
			if fnmatch.fnmatch(fname, "*_xhtml.py"):
				if os.path.isfile(os.path.join(root, fname[:-9]+'.stpy')):
					_unlink(root, fname)
				else:
					print "Skipped:", os.path.join(root,fname)
			if fnmatch.fnmatch(fname, "*-comp.log"):
				_unlink(root, fname)

		#print ">>>", root, dirs, files 

###

def main():
	parser = optparse.OptionParser()
	(options, args) = parser.parse_args()

	if len(args) != 1:
		parser.print_help()
		return 1

	cmd = args[0]

	if cmd == 'clean':
		return cmd_clean(options)

	return 0

if __name__ == "__main__":
	sys.exit(main())