#!/usr/bin/env strigapython

import random, sys, logging as L
import striga.server.serverapp, striga.core.exception

if __name__ == '__main__':

	# Initialize a pseudorandom number generator
	random.seed()

	try:
		app = striga.server.serverapp.ServerApplication()
		app.Run()
		sys.exit(0)

	except striga.core.exception.StrigaConfigurationError, e:
		L.exception("Exception during configuration")
		sys.stderr.write('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n')
		sys.stderr.write(str(e)+'\n')
		sys.stderr.write('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n')
		sys.exit(2)

#TODO: More exception handling
