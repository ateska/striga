#!/usr/bin/env strigapython

import sys, logging as L
import striga.compiler.compilerapp
import striga.core.exception

if __name__ == '__main__':
	try:

#TODO: Uncomment this for production
#		try:
#			import psyco
#			psyco.full()
#		except ImportError:
#			pass

		app = striga.compiler.compilerapp.CompilerApplication()
		app.Run()
		sys.exit(0)

	except striga.core.exception.StrigaConfigurationError, e:
		sys.stderr.write('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n')
		sys.stderr.write(str(e)+'\n')
		sys.stderr.write('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n')
		sys.exit(2)

	except striga.core.exception.StrigaFatalError, e:
		sys.stderr.write('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n')
		sys.stderr.write(str(e)+'\n')
		sys.stderr.write('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n')
		sys.exit(2)

	except Exception, e:
		sys.stderr.write('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n')
		sys.stderr.write(str(e)+'\n')
		sys.stderr.write('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n')
		#TODO: Write stack ...
		raise
		sys.exit(2)


#TODO: More exception handling
