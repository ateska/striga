import sys, os
import striga.external.spark.spark as spark
import striga.compiler.scanner as scanner
import striga.compiler.exception

###

class Parser(spark.GenericParser):


	def __init__(self, start = 'file_input'):
		spark.GenericParser.__init__(self, start)


	def parse(self, tokens):
		oldrecursionlimit = sys.getrecursionlimit()
		sys.setrecursionlimit(4000)
		try:
			return spark.GenericParser.parse(self, tokens)
		finally:
			sys.setrecursionlimit(oldrecursionlimit)


	def error(self, token):
		raise striga.compiler.exception.StrigaParserError(
			'Syntax error at or near %s' % token.GetLocationString()
		)


	def p_python_grammar(self, args):
		#Placeholder for grammar (it is loaded bellow)
		pass


	p_python_grammar.__doc__ = ""

	for line in file(os.path.join(os.path.dirname(__file__),'striga.bnf'),'r').readlines():
		if line.find("!") != 0 and line.find("#") != 0:
			p_python_grammar.__doc__ += line
			continue


###

import unittest, fnmatch

class TestCase(unittest.TestCase):


	@classmethod
	def Suite(cls):
		suite = unittest.TestSuite()

		for root, dirs, files in os.walk('../../'):
			for fn in files:
				if fnmatch.fnmatch(fn, '*.py'):
					fn = os.path.abspath(os.path.join(root, fn))
					suite.addTest(cls(fn))

		for root, dirs, files in os.walk('c:/python25'):
			for fn in files:
				if fnmatch.fnmatch(fn, '*.py'):
					fn = os.path.abspath(os.path.join(root, fn))
					fst = os.stat(fn)
					#Do not parse too long files ...
					if fst.st_size > 400000: continue
					suite.addTest(cls(fn))

#		suite.addTest(cls('./tests/classtest.py'))

		return suite


	def __init__(self, filename):
		unittest.TestCase.__init__(self)
		self.Filename = filename


	def shortDescription(self):
		return "Parser test on " + os.path.basename(self.Filename)


	def runTest(self):
		tokens = scanner.Scan(self.Filename)
		#print tokens
		parser = Parser()
		try:
			parser.parse(tokens)
			#print
		except Exception, e:
			print
			print "!!!!!!!!!!!!!!!!!!!!!!!!!!!"
			print e
			print "!!!!!!!!!!!!!!!!!!!!!!!!!!!"
			self.fail(str(e))


if __name__ == '__main__':
	os.chdir(os.path.dirname(__file__))
	suite = TestCase.Suite()
	unittest.TextTestRunner(verbosity=2).run(suite)
