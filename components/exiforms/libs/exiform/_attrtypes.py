import datetime, decimal

###

class AttrTypeBase(object):
	pass

###

class StringType(AttrTypeBase):


	def __init__(self, NoneIfEmpty = False):
		self.NoneIfEmpty = NoneIfEmpty


	def AttributeVAndT(self, ctx, value):
		if self.NoneIfEmpty and len(value) == 0:
			return None
		return value

###

class DecimalType(AttrTypeBase):


	def __init__(self, NoneIfEmpty = False):
		self.NoneIfEmpty = NoneIfEmpty


	def AttributeVAndT(self, ctx, value):
		if self.NoneIfEmpty and len(value) == 0:
			return None
		return decimal.Decimal(value)

###

class DateTimeType(AttrTypeBase):

	def AttributeVAndT(self, ctx, value):
		return datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
