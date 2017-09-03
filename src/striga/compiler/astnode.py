import tokenize, inspect
import striga.server.application
import striga.compiler.minicompiler as minicompiler
import striga.compiler.scanner as scanner
import striga.compiler.exception

###

class ASTNonTerminalNode:


	def __init__(self, type):
		self.type = type
		self._kids = []

	#
	#  Not all these may be needed, depending on which classes you use:
	#
	#  __getitem__		GenericASTTraversal, GenericASTMatcher
	#  __len__		GenericASTBuilder
	#  __setslice__		GenericASTBuilder
	#  __cmp__		GenericASTMatcher
	#

	def __getitem__(self, i):
		return self._kids[i]


	def __len__(self):
		return len(self._kids)


	def __setslice__(self, low, high, seq):
		self._kids[low:high] = seq


	def __cmp__(self, o):
		return cmp(self.type, o)


	def __repr__(self):
		return '<Nonterminal type="%s" nkids="%d">' % (self.type, len(self._kids))


	def GeneratePythonCode(self, identlevel = 0):
		ret = ""
		for kid in self._kids:
			if isinstance(kid, ASTNonTerminalNode):
				ret += kid.GeneratePythonCode(identlevel)
			else:

				if kid.pytype in (tokenize.NAME, tokenize.NUMBER):
					ret += kid.string + ' '

				elif kid.type == 'NEWLINE':
					ret = ret.rstrip(' \t')
					ret += '\n' + ('\t' * identlevel)

				elif kid.type == 'INDENT':
					identlevel += 1
					ret += '\t'

				elif kid.type == 'DEDENT':
					if ret[-1] != '\t':
						raise striga.compiler.exception.StrigaCompilerError("Dedenting on non-tabulators (found: `%s`) at or near %s" % (ret[-1], kid.GetLocationString()))
					identlevel -= 1
					ret = ret[:-1].rstrip(" \t") + '\n' + ('\t' * identlevel)

				else:
					if kid.string == '': continue
					if kid.string[0] in ('():.,><='): ret = ret.rstrip(' ')
					ret += kid.string

		return ret


	def Transform(self, cmodule):
		'''
Transform AST node into raw Python (overriden by Striga specific AST nodes)
		'''

		i = 0
		while i < len(self._kids):
			kid = self._kids[i]
			if isinstance(kid, ASTNonTerminalNode):
				ret = kid.Transform(cmodule)
				if ret is not None:
					self._kids[i:i+1] = ret
					i += len(ret) - 1

			i += 1


	def GetLocationString(self):
		for kid in self._kids:
			return kid.GetLocationString()

###

class ASTNode_striga_output_stmt(ASTNonTerminalNode):


	def Transform(self, cmodule):
		ASTNonTerminalNode.Transform(self, cmodule)

		TransformOutput = []
		OSMod =  cmodule.StrigaFileInfo.BuildMode.DefaultOutputStatementMod

		pos = 1
		while pos < len(self._kids):
			if self._kids[pos].type == ',':
				pos += 1
				continue

			if self._kids[pos].type == 'striga_output_flag':
				if len(self._kids[pos]._kids) == 3:
					if self._kids[pos]._kids[1].type == "~": OSMod = '~'
					else: OSMod = self._kids[pos]._kids[1].GeneratePythonCode().strip()
			else:
				if OSMod != '~':
					stmt = cmodule.StrigaFileInfo.BuildMode.TransformOutputStatement(cmodule, OSMod, self._kids[pos])
				else:
					stmt = "out.Write(%s)\n"  % (self._kids[pos].GeneratePythonCode())
				ast = minicompiler.CompileToAST('stmt_input', stmt, cmodule)._kids[:-1]
				TransformOutput.extend(ast)

			pos += 1

		if len(TransformOutput) > 0:
			del TransformOutput[-1] #Remove last NEWLINE from AST

		return TransformOutput

###

class TagbaseNode(ASTNonTerminalNode):


	def GetTagName(self):
		return self._kids[1].GeneratePythonCode().strip()


	def DetectActiveTag(self, tagname, cmodule, requiredmethods, args):
		taginst = cmodule

		for tagnamep in tagname.split('.'):

			if not hasattr(taginst, tagnamep):
				if taginst != cmodule:
					#Found tag library but not found object inside
					raise striga.compiler.exception.StrigaCompilerError("Cannot find active tag '%s' at or near %s (issue with '%s')" % (tagname, self._kids[0].GetLocationString(), tagnamep))
				return None

			taginst = getattr(taginst, tagnamep)

		for rm in requiredmethods:
			if not hasattr(taginst, rm):
				raise striga.compiler.exception.StrigaCompilerError("Cannot find active tag '%s' (found object do not have function '%s') at or near %s" % (tagname, rm, self._kids[0].GetLocationString()))

			fnct = getattr(taginst, rm)

			if not callable(fnct):
				raise striga.compiler.exception.StrigaCompilerError("Active tag '%s' function '%s' is not callable at or near %s" % (tagname, rm, self._kids[0].GetLocationString()))

			#Check if received call is not bounded class (aka object) methods
			if inspect.ismethod(fnct):
				if fnct.im_self is None:
					raise striga.compiler.exception.StrigaCompilerError("Active tag '%s' function '%s' is unbounded (probably not class or static method) at or near %s" % (tagname, rm, self._kids[0].GetLocationString()))

		#Arguments count check for first method
		startfnct = getattr(taginst, requiredmethods[0])
		if inspect.ismethod(startfnct):
			startfnct = startfnct.im_func
			startfnctcls = True
		else:
			startfnctcls = False

		#Format arguments into comparable format
		formatedargs = []
		if startfnctcls: formatedargs.append('cls')
		formatedargs.extend(['ctx','out'])

		formatedkwargs = None
		formatedaargs = None
		mode = None
		for arg in args:
			if arg.type=="striga_tagdefparameter":
				formatedargs.append(arg._kids[0].GeneratePythonCode().strip())
				mode = None
			elif arg.type=="striga_tagparam_sep" or arg.type==",":
				mode = None
			elif arg.type=="*":
				mode = 'args'
			elif arg.type=="**":
				mode = 'kwargs'
			elif arg.type=="identifier" and mode == 'args':
				formatedaargs = arg.GeneratePythonCode().strip()
				mode = None
			elif arg.type=="identifier" and mode == 'kwargs':
				formatedkwargs = arg.GeneratePythonCode().strip()
				mode = None
			else:
				raise striga.compiler.exception.StrigaCompilerError("Unexpected situation when parsing active tag parameters (tag: %s, arg: %s) at or near %s" % (tagname, arg.type, self._kids[0].GetLocationString()))

		definedargspec = inspect.getargspec(startfnct)
		receivedargspec = (formatedargs, formatedaargs, formatedkwargs, None)

#		#TODO: Do check defined vs received parameters
#		print ">>>>>>>>>>>>>", startfnct
#		print ">>>>>>>>>>>>>", definedargspec
#		print ">>>>>>>>>> VS", receivedargspec

		return taginst

###

class ASTNode_striga_ptag_stmt(TagbaseNode):


	def Transform(self, cmodule):
		ASTNonTerminalNode.Transform(self, cmodule)

		tagname = self.GetTagName()
		taginst = self.DetectActiveTag(tagname, cmodule, ["Start","End"], self._kids[2:-2])

		if taginst is None:
			#Static tag implementation
			TransformOutput = cmodule.StrigaFileInfo.BuildMode.TransformToPairTagStartAST(cmodule, tagname, self._kids[2:-2])

			if self._kids[-1]._kids[0].type == 'NEWLINE':
				TransformOutput.append(scanner.CreateNEWLINEToken())
				TransformOutput.extend(self._kids[-1]._kids[2:-1])
			else:
				TransformOutput.append(scanner.CreateNEWLINEToken())
				TransformOutput.extend(self._kids[-1]._kids)

			#Generate end tag
			TransformOutput.extend(
				cmodule.StrigaFileInfo.BuildMode.TransformToPairTagEndAST(cmodule, tagname, self._kids[2:-2])
			)
			TransformOutput.append(scanner.CreateNEWLINEToken())

			return TransformOutput

		pstmt = ""
		for kid in self._kids[2:-2]:
			if kid.type=="striga_tagparam_sep": pstmt += ','
			elif kid.type == "*": pstmt += '*'
			elif kid.type == "**": pstmt += '**'
			elif kid.type == ",":
				if pstmt[-1] != ',': pstmt += ','
			else: pstmt += kid.GeneratePythonCode()
		stmt = "%s.Start(ctx, out, %s)\n"  % (tagname, pstmt)
		TransformOutput = minicompiler.CompileToAST('stmt_input', stmt, cmodule)._kids[:-2]

		if self._kids[-1]._kids[0].type == 'NEWLINE':
			TransformOutput.append(scanner.CreateNEWLINEToken())
			TransformOutput.extend(self._kids[-1]._kids[2:-1])
		else:
			TransformOutput.append(scanner.CreateNEWLINEToken())
			TransformOutput.extend(self._kids[-1]._kids)

		stmt = "%s.End(ctx, out)\n"  % tagname
		TransformOutput.extend(minicompiler.CompileToAST('stmt_input', stmt, cmodule)._kids[:-1])

		return TransformOutput

###

class ASTNode_striga_stag_stmt(TagbaseNode):


	def Transform(self, cmodule):
		ASTNonTerminalNode.Transform(self, cmodule)

		tagname = self.GetTagName()
		taginst = self.DetectActiveTag(tagname, cmodule, ["Empty"], self._kids[2:])

		if taginst is None:
			#Static tag implementation (call to build mode API)
			return cmodule.StrigaFileInfo.BuildMode.TransformToSingletonTagAST(cmodule, tagname, self._kids[2:])

		pstmt = ""
		for kid in self._kids[2:]:
			if kid.type=="striga_tagparam_sep": pstmt += ','
			elif kid.type == "*": pstmt += '*'
			elif kid.type == "**": pstmt += '**'
			elif kid.type == ",":
				if pstmt[-1] != ',': pstmt += ','
			else: pstmt += kid.GeneratePythonCode()
		stmt = "%s.Empty(ctx, out, %s)\n"  % (tagname, pstmt)
		ast = minicompiler.CompileToAST('stmt_input', stmt, cmodule)._kids[:-1]

		return ast[:-1]

###

class ASTNode_striga_tagcall_stmt(TagbaseNode):

	def Transform(self, cmodule):
		ASTNonTerminalNode.Transform(self, cmodule)

		tagname = self.GetTagName()
		methodname = self._kids[3].GeneratePythonCode().strip()
		taginst = self.DetectActiveTag(tagname, cmodule, [methodname], self._kids[5:-1])

		if taginst is None:
			#Static tag implementation (call to build mode API)
			if methodname == 'Start':
				return cmodule.StrigaFileInfo.BuildMode.TransformToPairTagStartAST(cmodule, tagname, self._kids[5:-1])
			elif methodname == 'End':
				return cmodule.StrigaFileInfo.BuildMode.TransformToPairTagEndAST(cmodule, tagname, self._kids[5:-1])
			else:
				raise striga.compiler.exception.StrigaCompilerError("Invalid static tag method '%s' at or near %s" % (methodname, self._kids[0].GetLocationString()))

		#TODO: Implement active tag method call

###

class ASTNode_striga_import_stmt(ASTNonTerminalNode):


	def Transform(self, cmodule):
		ASTNonTerminalNode.Transform(self, cmodule)
		if self._kids[0].type == 'TAGIMPORT':
			return self.__TransfromTagImport(cmodule)

		#TODO: Other import styles ...

		return []


	def __TransfromTagImport(self, cmodule):

		names = []
		modules = []
		firsts = []

		i = 1
		while len(self._kids) > i:
			kid = self._kids[i]
			if len(kid._kids) == 1:
				n = kid.GeneratePythonCode().strip()
				modules.append(n)
				names.append(n.split('.')[0])
				firsts.append(True)
			elif len(kid._kids) == 3:
				modules.append(kid._kids[0].GeneratePythonCode().strip())
				names.append(kid._kids[2].string)
				firsts.append(False)
			else:
				raise striga.compiler.exception.StrigaCompilerError("Invalid tag library import statement at or near %s" % (self._kids[0].GetLocationString()))
			i += 2

		tagimportparams=[]
		for module, first in zip(modules, firsts):
			tagimportparams.append('("%s",%s)' % (module, str(first)))
		tagimportparams=",".join(tagimportparams)

		stmt = '(%s,) = striga.server.application.GetInstance().Services.Loader.TagImport(StrigaFileInfo, %s)\n' % (','.join(names),tagimportparams)
		ast = minicompiler.CompileToAST('stmt_input', stmt, cmodule)._kids[:-2]

		modimps = striga.server.application.GetInstance().Services.Loader.TagImport(cmodule.StrigaFileInfo, *zip(modules, firsts))

		for name, module in zip(names, modimps):
			if hasattr(cmodule, name):
				if getattr(cmodule, name) == module: continue
				raise striga.compiler.exception.StrigaCompilerError("Tag library import statement overrides previous one at or near %s" % (self._kids[0].GetLocationString()))
			setattr(cmodule, name, module)

		return ast

###

#TODO: This is HTML specific - should be moved into HTML specific part
import htmlentitydefs

class ASTNode_striga_entity(ASTNonTerminalNode):
	'''
&something
into
=|~|"&something;"
	'''

	def Transform(self, cmodule):

		entity = self._kids[1]._kids[0].string
		if not htmlentitydefs.name2codepoint.has_key(entity):
			raise striga.compiler.exception.StrigaCompilerError("Unknown HTML entity &%s; at or near %s" % (entity,self._kids[1]._kids[0].GetLocationString()))

		stmt = '=|~|"&%s;"\n'  % entity
		ast = minicompiler.CompileToAST('stmt_input', stmt, cmodule)._kids[:-1]
		del ast[-1]
		return ast
