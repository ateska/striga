import sys, os, optparse, glob, copy, codecs, new, compiler, logging as L
import striga.server.application, striga.core.context
import striga.core.exception, striga.core.sfinfo
import striga.service.compmngr, striga.service.loader
import striga.compiler.astbuilder as astbuilder
import striga.compiler.scanner as scanner

###

class CompilerApplication(striga.server.application.Application):

	CmdLineOptionList = striga.server.application.Application.CmdLineOptionList + [

		optparse.make_option(
					"-b", "--buildmode",
					action="append", dest="BuildModes", metavar="BUILDMODE",
					help="Set build mode(s) to BUILDMODE (more options can be given)"
		),

		optparse.make_option(
					"-p", "--path",
					action="append", dest="ComponentPath", metavar="COMPPATH",
					help="Add COMPPATH to component search path (more options can be given)"
		),

	]

	CmdLineDefaultOptions = dict(Config = 'striga-compiler.conf', **striga.server.application.Application.CmdLineDefaultOptions)

	def __init__(self):
		striga.server.application.Application.__init__(self, 'Striga Compiler')
		self.ExitCode = 0

		if self.CommandLineOptions.BuildModes is None:
			raise striga.core.exception.StrigaFatalError("At least one build mode must be specified")

		for filenameglob in self.CommandLineOptions.Args:
			for filename in glob.glob(filenameglob):
				self.ScheduleWorker(self.__RunCompilerWorker, filename, self.CommandLineOptions.BuildModes)

		self.ScheduleWorker(self.__SystemExitWorker)


	def _PrepareCoreServices(self):
		striga.server.application.Application._PrepareCoreServices(self)
		striga.service.loader.LoaderService(self.Services)
		striga.service.compmngr.ComponentManagerService(self.Services, self.CommandLineOptions.ComponentPath)


	def __RunCompilerWorker(self, filename, buildmodes):
		try:

			#Tokenize input file
			tokens = scanner.Scan(filename)

			#Parse tokens from input files into AST
			parser = astbuilder.ASTBuilder()
			ast = parser.parse(tokens)

			for buildmodename in buildmodes:
				try:
					buildmode = self.Services.ComponentManager.GetBuildMode(buildmodename)
				except striga.core.exception.StrigaRuntimeException:
					raise striga.core.exception.StrigaFatalError("Unknown build mode '%s'" % buildmodename)

				L.debug("Compiling '%s' in %s build mode" % (filename, buildmodename))
				self.__GenerateCode(copy.deepcopy(ast), buildmode, filename)

		except Exception, e:
			L.exception("Exception in compilation process")
			sys.stderr.write('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n')
			sys.stderr.write(str(e)+'\n')
			sys.stderr.write('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n')
			raise SystemExit(1)


	def __GenerateCode(self, ast, buildmode, filename):
		cmodule = new.module(os.path.splitext(os.path.basename(filename))[0] + '_' + buildmode.__name__[31:])
		cmodule.__file__ = os.path.abspath(filename)
		cmodule.StrigaFileInfo = striga.core.sfinfo.CompileTimeStrigaFileInfo(buildmode, cmodule.__file__)

		ast.Transform(cmodule)
		buildmode.EnhanceAST(cmodule, ast)

		#Generate Python code from AST
		codesrc = ast.GeneratePythonCode()
		outputfilename = os.path.splitext(filename)[0] + '_' + cmodule.StrigaFileInfo.BuildModeName + '.py'
		outfile = file(outputfilename, 'w')

		#DONT WRITE BOM because python refuses to compile code with both a UTF8 byte-order-mark and a magic encoding comment
		#outfile.write(codecs.BOM_UTF8)
		outfile.write("# -*- coding: utf-8 -*-\n")
		outfile.write(codesrc)
		outfile.close()

		#TODO: Following should be executed only if command-line param is requiring that
		compiler.compileFile(outputfilename)


	def __SystemExitWorker(self):
		sys.exit(self.ExitCode)

