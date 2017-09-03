#This module contains functions and classes to support MVC architecture

class CallView(object):

	def __init__(self, *args, **kwargs):
		self.Args = args
		self.KWArgs = kwargs

###

class CallViewWithPath(CallView):

	def __init__(self, path, *args, **kwargs):
		CallView.__init__(self, *args, **kwargs)
		self.Path = path

NoView = False
