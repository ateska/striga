import striga.core.exception

###

class _NotDefined(object): pass

###

class SetVariables(object):
	'''
Container that will implicitily return every attribute as Variables class.
Usable for creating 'sub-namespace' of Variables.

Example:
	sv = SetVariables()
	sv.AddVarSet('POST', MultiDict())
	sv.POST['v'] = 1
	sv.POST['v'] += 1
	'''

	def __init__(self):
		self.__setvars = set()


	def AddVarSet(self, name, varset):
		setattr(self, name, varset)
		self.__setvars.add(name)


	def __repr__(self):
		return "<{0} {1}>".format(self.__class__.__name__, ', '.join(self.__setvars))
###

class MultiDict(dict):


	def __init__(self, initload = []):
		dict.__init__(self)
		self.Update(initload)


	def Set(self, key, *values):
		dict.__setitem__(self, key, list(values))


	def Add(self, key, *values):
		dict.setdefault(self, key, []).extend(values)


	def GetAll(self, key, *values):
		#TODO: This method has an issue:
		#- if i want to receive empty list when key was not found,
		#i have no way how to do it
		ret = dict.get(self, key, values)

		if len(ret) == 0:
			if dict.has_key(self, key): dict.__delitem__(self, ret)
			raise KeyError("Key '%s' not found in MultiDict" % key)

		return ret



	def GetOne(self, key, default = _NotDefined):
		'This is better approach than Get() ... remark mainly for striga2'

		try:
			return self.GetAll(key)[0]
		except KeyError:
			if default is not _NotDefined: return default
			raise

		# TODO: Handle non-existing situation (empty array)


	def Get(self, key, index = 0, *values):
		return self.GetAll(key, *values)[index]


	def Pop(self, key, *values):
		arr = self.GetAll(key, *values)
		ret = arr[0]
		del arr[0]
		if len(arr) == 0: dict.__delitem__(self, key)
		return ret


	def SetDefault(self, key, *values):
		return dict.setdefault(self, key, list(values))


	def __len__(self):
		ret = 0
		for a in dict.values(self):
			ret += len(a)
		return ret


	def iteritems(self):
		for k, a in dict.iteritems(self):
			for i in iter(a):
				yield (k,i)


	def items(self):
		return list(self.iteritems())


	def itervalues(self):
		for k, a in dict.iteritems(self):
			for i in iter(a):
				yield i


	def values(self):
		return list(self.itervalues())


	def popitem(self):
		k,v = dict.popitem(self)
		ret = v[-1]
		del v[-1]
		if len(v) > 0:
			dict.__setitem__(self, k, v)
		return k, ret


	def Update(self, load):
		if isinstance(load, list):
			for k, a in load:
				for i in a:
					self.Add(k, i)
		elif isinstance(load, dict):
			for k, a in load.iteritems():
				for i in a:
					self.Add(k, i)


	def Remove(self, key, item):
		arr = dict.get(self, key)
		arr.remove(item)
		if len(arr) == 0: dict.__delitem__(self, key)


	@classmethod
	def fromkeys(cls, keyseq, *values):
		nmd = cls()
		for key in keyseq:
			nmd.Set(key, *values)
		return nmd


	__getitem__ = Get
	__setitem__ = Set
	get = Get
	pop = Pop
	setdefault = SetDefault
	update = Update

###

class StackDict(object):


	def __init__(self):
		self.__Dict = dict()


	def push(self, stackvarname, value):
		try:
			stack = self.__Dict[stackvarname]
		except KeyError:
			stack = []
			self.__Dict[stackvarname] = stack 
		
		stack.append(value)


	def pop(self, stackvarname):
		try:
			stack = self.__Dict[stackvarname]
		except KeyError:
			raise striga.core.exception.StrigaStackEmptyException()
		
		val = stack.pop()
		if len(stack) == 0:
			del self.__Dict[stackvarname]
		return val


	def front(self, stackvarname):
		try:
			stack = self.__Dict[stackvarname]
		except KeyError:
			raise striga.core.exception.StrigaStackEmptyException()
		return stack[-1]


	def has_key(self, key):
		return self.__Dict.has_key(key)
