from ._attrtypes import StringType

###

class Attribute(object):


	def __init__(self, name, label=None, newvalue=None, type=None, readonly=False, css={}):
		self.Name = name
		self.Label = label if label is not None else name
		self.NewValue = newvalue
		self.ReadOnly = readonly
		self.CSS = css

		if type is None:
			self.Type = StringType()
		else:
			self.Type = type


	def AttributeVAndT(self, ctx, value):
		# Attribute level Validation and Transformation (Actually just pass this to the attribute type VAndT)
		return self.Type.AttributeVAndT(ctx, value)

###

class LookupAttribute(Attribute):


	def __init__(self, name, options_generator, label=None, newvalue=None, type=None, readonly=False, css={}):
		Attribute.__init__(self, name, label=label, newvalue=newvalue, type=type, readonly=readonly, css=css)
		self.__Options = None # Tuple (<id>, <name>, ...)
		self.OptionsGenerator = options_generator


	def GetOptions(self):
		if self.__Options is None:
			self.__Options = self.OptionsGenerator()
		return self.__Options
