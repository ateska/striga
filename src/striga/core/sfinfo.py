
class StrigaFileInfoSuperclass(object):
	'''
	Superclass for all StrigaFileInfo classes
	'''
	pass

###

class CompileTimeStrigaFileInfo(StrigaFileInfoSuperclass):
	'''
	Used in compile process
	'''

	def __init__(self, buildmode, filename):
		self.BuildMode = buildmode
		self.BuildModeName = buildmode.__name__[31:]
		self.FileName = filename
		DefaultOut = None
