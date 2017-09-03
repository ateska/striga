import sys, imp

###

def DoImport(name, paths, namesysprefix):
	# Fast path: see if the module has already been imported.
	try:
		return sys.modules[namesysprefix + name]
	except KeyError:
		pass


	fp, pathname, description = imp.find_module(name, paths)

	try:
		return imp.load_module(namesysprefix + name, fp, pathname, description)
	finally:
		# Since we may exit via an exception, close fp explicitly.
		if fp:
			fp.close()
