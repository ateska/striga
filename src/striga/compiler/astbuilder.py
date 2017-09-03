import os
import striga.external.spark.spark as spark
import striga.compiler.parser as parser
import striga.compiler.scanner as scanner
import striga.compiler.astnode as astnode
import striga.compiler.astutils as astutils
import striga.compiler.exception

###

class ASTBuilder(parser.Parser):


	def __init__(self, start = 'file_input'):
		parser.Parser.__init__(self, start)


	def preprocess(self, rule, func):
		rebind = lambda lhs, self=self: lambda args, lhs=lhs, self=self: self.buildASTNode(args, lhs)
		lhs, rhs = rule
		return rule, rebind(lhs)


	def buildASTNode(self, args, lhs):
		children = []
		for varg in args:

			#Arg can be array in case of 'array' type
			if not isinstance(varg, list):
				varg = [varg,]
			for arg in varg:
				if isinstance(arg, astnode.ASTNonTerminalNode):
					children.append(arg)
				else:
					children.append(self.terminal(arg))

		#When node is 'array' type, skip its creation and return array of children
		if lhs in self.ArrayTypes:
			return children

		#Check 'pass' types
		if len(children) == 1:
			if lhs in self.PassTypes:
				return children[0]

		return self.nonterminal(lhs, children)


	def terminal(self, token):
		return token


	def nonterminal(self, type, args):
		rv = getattr(astnode, 'ASTNode_' + type, astnode.ASTNonTerminalNode)(type)
		rv[:len(args)] = args
		return rv


	def parse(self, tokens):
		ast = parser.Parser.parse(self, tokens)
		return ast


	ArrayTypes = set()
	PassTypes = set()

	for line in file(os.path.join(os.path.dirname(__file__),'striga.bnf'),'r').readlines():
		if line.find("!") == 0:

			if line.find("array:") == 1:
				ArrayTypes.add(line[7:].strip())

			elif line.find("pass:") == 1:
				PassTypes.add(line[6:].strip())

			else:
				raise striga.compiler.exception.StrigaCompilerError("Invalid gramar definition '%s'" % line.strip())


###

import unittest, fnmatch, os

class TestCase(unittest.TestCase):


	@classmethod
	def Suite(cls):
		suite = unittest.TestSuite()

#		for root, dirs, files in os.walk('../../'):
#			for fn in files:
#				if fnmatch.fnmatch(fn, '*.py'):
#					fn = os.path.abspath(os.path.join(root, fn))
#					suite.addTest(cls(fn))

#		for root, dirs, files in os.walk('c:/python25'):
#			for fn in files:
#				if fnmatch.fnmatch(fn, '*.py'):
#					fn = os.path.abspath(os.path.join(root, fn))
#					fst = os.stat(fn)
#					#Do not parse too long files ...
#					if fst.st_size > 400000: continue
#					suite.addTest(cls(fn))

		suite.addTest(cls('./tests/simplepage.stpy'))

		return suite


	def __init__(self, filename):
		unittest.TestCase.__init__(self)
		self.Filename = filename


	def shortDescription(self):
		return "AST Builder test on " + os.path.basename(self.Filename)


	def runTest(self):
		#Tokenize input file
		tokens = scanner.Scan(self.Filename)

		#Parse tokens from input files into AST
		parser = ASTBuilder()
		ast = parser.parse(tokens)

		#TODO: [unittest] Prepare parameters
		ast.Transform()

		#astutils.DumpAST2MindMap(ast, 'ast.mm')

		#Generate Python code from AST
		codesrc = ast.GeneratePythonCode()

		#print >> file('___OUTPUT___.py','w'), codesrc

		#Compile it
		compile(codesrc, 'Reincarnation of ' + self.Filename, 'exec')


if __name__ == '__main__':

	os.chdir(os.path.dirname(__file__))
	suite = TestCase.Suite()
	unittest.TextTestRunner(verbosity=2).run(suite)
