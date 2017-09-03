
def StrigaViewEntry(fnct):
	'''
	This is decorator for striga view methods
	'''
	fnct.StrigaViewEntry = True
	return fnct

###

class PairTag(object):

	@classmethod
	def Empty(cls, ctx, out, *args, **kwargs):
		'''
		Shortcut for Start and End call - no compile time checking!
		'''
		cls.Start(ctx, out, *args, **kwargs)
		cls.End(ctx, out)

###

class SingletonTag(object):
	pass
