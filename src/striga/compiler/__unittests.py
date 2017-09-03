import unittest
import glob, os, fnmatch
import striga.compiler.scanner

####

#TODO: Move here other use cases
class TestCase(unittest.TestCase):

	def setUp(self):
		unittest.TestCase.setUp(self)


	def tearDown(self):
		unittest.TestCase.tearDown(self)


	def testScannerBasic(self):
		for filename in glob.glob('./tests/*.py'):
			striga.compiler.scanner.Scan(filename)

		for filename in glob.glob('./tests/*.stpy'):
			striga.compiler.scanner.Scan(filename)


	def testScannerWholeStriga(self):
		for root, dirs, files in os.walk('../../'):
			for fn in files:
				if fnmatch.fnmatch(fn, '*.py'):
					filename = os.path.abspath(os.path.join(root, fn))
					striga.compiler.scanner.Scan(filename)

				if fnmatch.fnmatch(fn, '*.stpy'):
					filename = os.path.abspath(os.path.join(root, fn))
					striga.compiler.scanner.Scan(filename)


#TODO: Uncomment this ...
#	def testScannerWholePython(self):
#		for root, dirs, files in os.walk(os.path.dirname(os.__file__)):
#			for fn in files:
#				if fnmatch.fnmatch(fn, '*.py'):
#					filename = os.path.abspath(os.path.join(root, fn))
#					striga.compiler.scanner.Scan(filename)


####

if __name__ == '__main__':
	unittest.main()
