import sys, os, tokenize, logging as L
import striga.core.exception
import striga.server.application
import striga.external.spark.spark

###

class Token:

	def __init__(self, type, attr=None, lineno='???'):
		self.type = type
		self.attr = attr
		self.lineno = lineno


	def __cmp__(self, o):
		return cmp(self.type, o)


	def __repr__(self):
		return str(self.type)


_map = {
	tokenize.ENDMARKER	: 'ENDMARKER',
	tokenize.NAME 		: 'NAME',
	tokenize.NUMBER		: 'NUMBER',
	tokenize.STRING		: 'STRING',
	tokenize.NEWLINE	: 'NEWLINE',
	tokenize.INDENT		: 'INDENT',
	tokenize.DEDENT		: 'DEDENT',
}

###

class PreprocessedFile(object):

	def __init__(self, filename):
		self.FileStack = []
		self.__AddFileToStack(filename)


	def __AddFileToStack(self, filename):
		try:
			f = open(filename, 'r')
		except IOError, (errno, strerror):
			raise striga.core.exception.StrigaConfigurationError("Problem when opening configuration file: " + strerror,filename)

		self.FileStack.append(f)


	def __call__(self):
		line = self.FileStack[-1].readline()
		if len(line) == 0:
			self.FileStack.pop().close()
			if len(self.FileStack) == 0: return ""
			line = self.FileStack[-1].readline()

		if line.find("!include ") == 0:
			self.__AddFileToStack(line[9:].strip())
			return self()

		if line.find('!conffile') == 0:
			app = striga.server.application.GetInstance()
			if app is None:
				raise RuntimeError("Directive !conffile can be used only in Application mode")
			try:
				inpf = file(line[10:].strip(),'r')
			except:
				raise striga.core.exception.StrigaConfigurationError("Cannot find configuration file '%s' given by !conffile directive" % line[10:].strip())
			for line in inpf:
				line = line.rstrip()
				if len(line) == 0: continue
				if line[0] == '#' or line[0] == ';': continue
				key, value = line.split('=',1)
				value = value.strip()
				key = key.strip()
				app.ConfigDictionary[key] = value
			return self()

		return line

###

class Config(object):


	def __init__(self, services, filename, confdefs, lateloads):

		f = PreprocessedFile(filename)

		tokens = []
		for ttype, tstring, sloc, eloc, linetxt in tokenize.generate_tokens(f):
			if ttype in (tokenize.COMMENT, tokenize.NL): continue

			attr = tstring

			if _map.has_key(ttype):
				type = _map[ttype]
			else:
				type = tstring

			tokens.append(Token(type, attr=attr, lineno=sloc[0]))

		parser = ConfigParser(filename)
		confchilds = parser.parse(tokens)
		self.ConfFilename = os.path.abspath(filename)
		self.__configure(services, filename, confchilds, confdefs, lateloads)


	def __configure(self, services, filename, confchilds, confdefs, lateloads = {}):
		for ch in confchilds:
			while 1:
				try:
					fn = confdefs[ch.Name]
				except KeyError:

					#Check lateloads
					if lateloads.has_key(ch.Name):
						if not sys.modules.has_key(lateloads[ch.Name][0]):
							mod = __import__(lateloads[ch.Name][0])
							components = lateloads[ch.Name][0].split('.')
							for comp in components[1:]:
								mod = getattr(mod, comp)
						else:
							mod = sys.modules[lateloads[ch.Name][0]]

						#Create instance of new service class and get config defs from that
						ns = getattr(mod, lateloads[ch.Name][1])(services)
						confdefs.update(ns.GetConfigDefs())
						continue

					raise striga.core.exception.StrigaConfigurationError("Unknown configuration definition: " + ch.Name, filename, ch.LineNo)

				childconfdefs = fn(self.ConfFilename, **ch.Args)

				if (childconfdefs is not None) and hasattr(ch, 'Childs'):
					self.__configure(services, filename, ch.Childs, childconfdefs)
				elif (childconfdefs is not None) and not hasattr(ch, 'Childs'):
					#When object defines childs but not found in configuration,
					#provide empty child list - this will ensure '!' rule to be executed
					self.__configure(services, filename, {}, childconfdefs)
				elif (childconfdefs is None) and hasattr(ch, 'Childs'):
					raise striga.core.exception.StrigaConfigurationError("Configuration definition '%s' does not support childs" % ch.Name, filename, ch.LineNo)

				break

		if confdefs.has_key('!'):
			confdefs['!']()

###

class ConfigDefinition(object):


	def __init__(self, lineno, name, args, childs = None):
		self.LineNo = lineno
		self.Name = name
		self.Args = args
		if childs is not None:
			self.Childs = childs


	def __str__(self):
		return "<Name: %s>" % self.Name

###

class ConfigParser(striga.external.spark.spark.GenericParser):

	ProtectedNames = frozenset((
		'from',
	))

	def __init__(self, filename):
		striga.external.spark.spark.GenericParser.__init__(self, 'file_input')
		self.Filename = filename


	def error(self, token):
		raise striga.core.exception.StrigaConfigurationError(
			'Syntax error at or near "%s"' % token.attr,
			self.Filename, token.lineno
		)


	def p_file_input(self, args):
		'''
			file_input ::= file_contents ENDMARKER
		'''
		return args[0]


	def p_file_contents_1(self, args):
		'''
			file_contents ::= file_contents NEWLINE
			file_contents ::= file_contents stmt
		'''
		args[0].append(args[1])
		return args[0]


	def p_file_contents_2(self, args):
		'''
			file_contents ::=
		'''
		return []


	def p_stmt(self, args):
		'''
			stmt ::= small_stmt
			stmt ::= compound_stmt
		'''
		return args[0]


	def p_small_stmt(self, args):
		'''
			small_stmt ::= one_line_define_stmt NEWLINE
			small_stmt ::= one_line_define_stmt ; NEWLINE
		'''
		return args[0]


	def p_one_line_define_stmt_1(self, args):
		'''
			one_line_define_stmt ::= NAME
		'''
		return ConfigDefinition(args[0].lineno, args[0].attr, {})


	def p_one_line_define_stmt_2(self, args):
		'''
			one_line_define_stmt ::= NAME parameters
		'''
		return ConfigDefinition(args[0].lineno, args[0].attr, args[1])


	def p_compound_stmt_1(self, args):
		'''
			compound_stmt ::= NAME : suite
		'''
		return ConfigDefinition(args[0].lineno, args[0].attr, {}, args[2])


	def p_compound_stmt_2(self, args):
		'''
			compound_stmt ::= NAME parameters : suite
		'''
		return ConfigDefinition(args[0].lineno, args[0].attr, args[1], args[3])


	def p_suite(self, args):
		'''
			suite ::= NEWLINE INDENT stmt_list DEDENT
		'''
		return args[2]


	def p_stmt_list_1(self, args):
		'''
			stmt_list ::= stmt_list stmt
		'''
		args[0].append(args[1])
		return args[0]


	def p_stmt_list_2(self, args):
		'''
			stmt_list ::= stmt
		'''
		return args


	def p_parameters_1(self, args):
		'''
			parameters ::= ( argslist )
		'''
		return args[1]


	def p_parameters_2(self, args):
		'''
			parameters ::= ( )
		'''
		return {}


	def p_argslist_1(self, args):
		'''
			argslist ::= argslist , NAME = atom
		'''
		if args[2].attr in self.ProtectedNames: args[2].attr += '_'
		args[0][args[2].attr] = args[4]
		return args[0]


	def p_argslist_2(self, args):
		'''
			argslist ::= NAME = atom
		'''
		if args[0].attr in self.ProtectedNames: args[0].attr += '_'
		return {args[0].attr : args[2]}


	def p_atom_1(self, args):
		'''
			atom ::= NAME
		'''
		app = striga.server.application.GetInstance()
		if app is not None:
			v = app.ConfigDictionary.get(args[0].attr, None)
			if v is not None: return v
		raise RuntimeError("Cannot find configuration variable '%s'" % args[0].attr) 


	def p_atom_2(self, args):
		'''
			atom ::= STRING
		'''
		return str(eval(args[0].attr))


	def p_atom_3(self, args):
		'''
			atom ::= NUMBER
		'''
		return eval(args[0].attr)
