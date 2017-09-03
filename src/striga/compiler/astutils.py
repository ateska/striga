import time, xml.sax.saxutils
import striga.compiler.astnode as astnode
import striga.compiler.scanner as scanner

###

def DumpAST2MindMap(ast, filename):

	def _DumpAST2File(ast, f):
		ctime = int(time.time())

		f.write('<node CREATED="%d" ID="Freemind_Link_%d" MODIFIED="%d" TEXT=%s POSITION="right" BACKGROUND_COLOR="#9999ff">\n' % (ctime, ctime, ctime, xml.sax.saxutils.quoteattr(ast.type)))
		f.write('<font BOLD="true" NAME="SansSerif" SIZE="12"/>\n')
		for kid in ast._kids:
			if isinstance(kid, astnode.ASTNonTerminalNode):
				_DumpAST2File(kid, f)
			else:
				f.write('<node CREATED="%d" ID="Freemind_Link_%d" MODIFIED="%d" TEXT=%s POSITION="right" />\n' % (ctime, ctime, ctime, xml.sax.saxutils.quoteattr(kid.type + ":" + kid.string)))

		f.write('</node>\n')

	f = file(filename,'w')
	f.write('<map version="0.8.0">\n')
	_DumpAST2File(ast,f)
	f.write('</map>\n')

###

def CommonEnhanceAST(cmodule, ast):
	import striga.compiler.minicompiler as minicompiler

	stmt = """
class StrigaFileInfo(striga.core.sfinfo.StrigaFileInfoSuperclass):
	BuildModeName = '%(BuildModeName)s'
	BuildMode = striga.server.application.GetInstance().Services.ComponentManager.GetBuildMode(BuildModeName)
	FileName = __file__
""" % {'BuildModeName' : cmodule.StrigaFileInfo.BuildModeName}
	newast = minicompiler.CompileToAST('stmt_input', stmt, cmodule)._kids[:-1]
	ast._kids[0:0] = newast

	stmt = "from commonspace import *\n"
	newast = minicompiler.CompileToAST('stmt_input', stmt, cmodule)._kids[:-1]
	ast._kids[0:0] = newast

	stmt = "import striga.core.sfinfo\n"
	newast = minicompiler.CompileToAST('stmt_input', stmt, cmodule)._kids[:-1]
	ast._kids[0:0] = newast

	stmt = "import striga.server.application\n"
	newast = minicompiler.CompileToAST('stmt_input', stmt, cmodule)._kids[:-1]
	ast._kids[0:0] = newast

###

def FindASTLocation(ast, query):

	if query.find(' ') > 0:
		qpart, qleft = query.split(' ',1)
	else:
		qpart = query
		qleft = None

	for kid in ast._kids:
		if isinstance(kid, astnode.ASTNonTerminalNode):
			if kid.type == qpart:
				if qleft is not None:
		 			ret = FindASTLocation(kid, qleft)
					if ret is None: continue

				return kid

		elif isinstance(kid, scanner.ASTTerminalNode):
			if kid.string == qpart:
				if qleft is not None:
					return None
				else:
					return kid
		else:
			raise  RuntimeError("Unknown AST node type %s" % str(type(kid)))

	return None
