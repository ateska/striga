from ._attributes import Attribute
import itertools

###

class _DescriptorValues(object):

	def __init__(self, idict = {}):
		self.__dict__.update(idict)

###

class Descriptor(object):


	IDItemDef = Attribute(
			name='id',
			newvalue = 'new'
			)

	ItemDefs = None	# This class attribute must be overloaded by implementation (content is list of Attributes)
	_ItemDefsMap = dict()

	DisabledActions = [] # List of codes of actions that are not supported by the form

	def __init__(self, controller, viewmode):
		self.Items = None
		self.Action = None # One of None, 'Insert', 'Update' or 'Delete'
		self.ViewMode = viewmode # One of 'new', 'show', 'edit'
		self.Controller = controller
		self.Valid = None # One of None, True, False

		if len(self._ItemDefsMap) == 0:
			for a in itertools.chain(self.ItemDefs, [self.IDItemDef]):
				self._ItemDefsMap[a.Name] = a


	def InitItemsAsNew(self, ctx):
		self.Items = _DescriptorValues(dict([(a.Name, a.NewValue) for a in itertools.chain(self.ItemDefs, [self.IDItemDef])]))


	def InitItems(self, items):
		self.Items = items


	def GetAttributeDescriptor(self, name):
		return self._ItemDefsMap[name]


	def GetID(self):
		return getattr(self.Items, self.IDItemDef.Name)


	def FormVAndT(self, ctx, newitems):
		# Attribute level Validation and Transformation
		return newitems


	def ValidateAndTransform(self, ctx):
		self.Valid = None

		# Launch attribute level V(alidations) and T(ranformations)
		newitems = {}
		for itemdef in itertools.chain([self.IDItemDef], self.ItemDefs):
			newitems[itemdef.Name] = itemdef.AttributeVAndT(ctx, self.Items[itemdef.Name])

		# Launch form level V(alidations) and T(ranformations), also convert dict of new items into _DescriptorValues
		newitems = self.FormVAndT(ctx, _DescriptorValues(newitems))

		if self.Valid is None:
			self.Valid = True
			self.InitItems(newitems)
