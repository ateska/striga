###

class XHtmlOut(object):
	'''
This class represent 'filter' for striga views outputs to ctx.res
	'''

	def __init__(self, writefnct):
		self.WriteFnct = writefnct


	def Write(self, txt):
		#If str() is needed, use _striga_xhtml_str from xhtmlspace
		self.WriteFnct(txt)
