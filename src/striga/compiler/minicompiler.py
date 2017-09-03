import StringIO

###

def CompileToAST(init_rule, stmt, cmodule):
	'''
Used by AST node during transformation to create new AST nodes
	'''

	infile = StringIO.StringIO(stmt)

	import striga.compiler.scanner as scanner
	tokens = scanner.Scan(infile.readline)

	import striga.compiler.astbuilder as astbuilder
	parser = astbuilder.ASTBuilder(start = init_rule)
	ast = parser.parse(tokens)

	ast.Transform(cmodule)

	return ast