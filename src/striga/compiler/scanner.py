import tokenize

###

class ASTTerminalNode(object):
	'''
Or token ...
	'''

	SpecPyTokensMap = {
		tokenize.ENDMARKER	: 'ENDMARKER',
		tokenize.NAME 		: 'NAME',
		tokenize.NUMBER		: 'NUMBER',
		tokenize.STRING		: 'STRING',
		tokenize.NEWLINE	: 'NEWLINE',
		tokenize.INDENT		: 'INDENT',
		tokenize.DEDENT		: 'DEDENT',
	}

	ReservedWords = frozenset([
		'and',
		'as',
		'assert',
		'break',
		'class',
		'continue',
		'def',
		'del',
		'elif',
		'else',
		'except',
		'exec',
		'finally',
		'for',
		'from',
		'global',
		'if',
		'import',
		'in',
		'is',
		'lambda',
		'not',
		'or',
		'pass',
		'print',
		'raise',
		'return',
		'try',
		'while',
		'with',
		'yield',

		'tagimport',
	])


	def __init__(self, ttype, tstring, sloc, eloc, linetxt, filename):
		self.pytype = ttype
		self.string = tstring
		self.sloc = sloc
		self.eloc = eloc
		self.linetxt = linetxt
		self.filename = filename

		#Translate Python token type into spark one
		if self.SpecPyTokensMap.has_key(ttype):
			if tstring in self.ReservedWords:
				self.type = tstring.upper()
			else:
				self.type = self.SpecPyTokensMap[ttype]
		else:
			self.type = tstring

		#Nice name for non-printable token
		if ttype == tokenize.NEWLINE:
			self.string = '<end of line>'
		elif ttype == tokenize.INDENT:
			self.string = '<indenting>'
		elif ttype == tokenize.DEDENT:
			self.string = '<dedenting>'


	def __cmp__(self, o):
		return cmp(self.type, o)


	def __repr__(self):
		return '<ASTTerminalNode type="%s" string="%s">' % (self.type, self.string)


	#This is for AST traversal - Token is playing there role of terminal
	def __getitem__(self, i):
		raise IndexError()


	def GetLocationString(self):
		return '"%s":\n  File "%s", line %d, column %d\n%s' % (self.string, self.filename, self.sloc[0], self.sloc[1], self.linetxt.rstrip())


###

def CreateNEWLINEToken(sloc = 0, eloc = 0, linetxt = "", filename = ""):
	return ASTTerminalNode(tokenize.NEWLINE,'<end-of-line>', sloc, eloc, linetxt, filename)

###

def Scan(inputfile, filename = '<internal>'):
	if isinstance(inputfile, basestring):
		f = ExtReadLine(inputfile)
		filename = inputfile
	else:
		f = inputfile
		filename = filename

	tokens = []
	for ttype, tstring, sloc, eloc, linetxt in tokenize.generate_tokens(f):
		if ttype in (tokenize.COMMENT, tokenize.NL): continue
		tokens.append(ASTTerminalNode(ttype, tstring, sloc, eloc, linetxt, filename))

	return tokens

###

class ExtReadLine(object):


	def __init__(self, f):
		self.__f = open(f, 'r')


	def __call__(self):
		if self.__f is not None:
			r = self.__f.readline()
			if r != '' and r[-1] != '\n':
				r += '\n'
			if r == '':
				r = '\n'
				self.__f = None
			return r
		else:
			return ''
