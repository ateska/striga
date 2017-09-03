import logging as L
import striga.core.exception
import striga.compiler.minicompiler as minicompiler
import striga.compiler.astutils as astutils

###

DefaultOutputStatementMod = 'h'
DocumentHeader = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\n'
DocumentHeader_HTML5 = '<!DOCTYPE html>\n'

#TODO: Following (must implement handling of * and ** parameters in static tags
#HTMLTagParams = {"xmlns":"http://www.w3.org/1999/xhtml"}

###

def _ExtractParamName(kid):
	#Resolve collision of two worlds
	if kid._kids[0].type == 'CLASS':
		paramname = "class"
	elif kid._kids[0].type == 'FOR':
		paramname = "for"
	elif kid._kids[0].type == 'STRING':
		paramname = eval(kid._kids[0].string)
	else:
		paramname = kid._kids[0]._kids[0]._kids[0].string

#	paramname = paramname.replace('-','__')

	return paramname

###

def _TransformToTagStartAST(cmodule, tagname, kids, tagending):
	if len(kids) == 0:
		#stmt = '_striga_xhtml_tag(out, "<{0}", "{1}>", None)\n'.format(tagname.replace(".",":").lower(), tagending)
		# ... following line is optimization
		stmt = 'out.Write("<%s%s>")\n' % (tagname.replace(".",":").lower(), tagending)
	else:
		fnctname = '_striga_xhtml_tag'
		beginstmt = '(out, "<{0}", "{1}>", ('.format(tagname.replace(".",":").lower(), tagending)

		params = []
		kwparams = ""

		kids = list(kids)
		while 1:
			try:
				kid = kids.pop(0)
			except IndexError:
				break

			if kid.type == 'striga_tagparam_sep':
				pass

			elif kid.type == 'striga_tagdefparameter':
				paramname = _ExtractParamName(kid)
				params.append('"{0}",{1}'.format(paramname, kid._kids[2].GeneratePythonCode().strip()))

			elif kid.type == '**':
				fnctname = '_striga_xhtml_tagkw'
				param = kids.pop(0)
				kwparams = ', **' + param.GeneratePythonCode().strip()
				pass

			else:
				L.warning("Unknown AST node '%s' in static start tag '%s'" % (kid.type, tagname))

		#TODO: There is an optimization possible - if all childs are static strings, tag can be "printed" during compile time

		stmt = fnctname + beginstmt + (', '.join(params)) + ')' + kwparams + ')\n'

	ast = minicompiler.CompileToAST('stmt_input', stmt, cmodule)._kids[:-1]
	del ast[-1]
	return ast


def TransformToSingletonTagAST(cmodule, tagname, kids):
	'''
	API function
	Called to generate static signleton tag AST
	'''
	return _TransformToTagStartAST(cmodule, tagname, kids, ' /')


def TransformToPairTagStartAST(cmodule, tagname, kids):
	'''
	API function
	Called to generate static pair tag (start) AST
	'''
	return _TransformToTagStartAST(cmodule, tagname, kids, '')


def TransformToPairTagEndAST(cmodule, tagname, kids):
	'''
	API function
	Called to generate static pair tag (end) AST
	'''
	stmt = 'out.Write("</%s>")\n' % tagname.replace(".",":").lower()
	ast = minicompiler.CompileToAST('stmt_input', stmt, cmodule)._kids[:-1]
	del ast[-1]
	return ast


def TransformOutputStatement(cmodule, osmod, kid):
	if osmod == 'h':
		return "out.Write(_striga_xhtml_escape(%s))\n"  % (kid.GeneratePythonCode())
	else:
		raise striga.compiler.exception.StrigaCompilerError("Unsupported output modificator '%s' for xhtml build mode at or near %s" % (osmod, kid.GetLocationString()))


def EnhanceAST(cmodule, ast):
	'''
	API function
	Called to add headers and tails to generated source code
	'''

	stmt = "from xhtmlspace import _striga_xhtml_escape, _striga_xhtml_tag, _striga_xhtml_tag, _striga_xhtml_tagkw\n"
	asthead = minicompiler.CompileToAST('stmt_input', stmt, cmodule)._kids[:-1]

	astutils.CommonEnhanceAST(cmodule, ast)
	ast._kids[0:0] = asthead

	#Find StrigaFileInfo and insert this line into a class
	sfdescr = astutils.FindASTLocation(ast, "classdef classname identifier StrigaFileInfo")

	stmt = "from xhtmlout import XHtmlOut as DefaultOut\n"
	sfdescr._kids[-1][-1:-1] = minicompiler.CompileToAST('stmt_input', stmt, cmodule)._kids[:-1]
