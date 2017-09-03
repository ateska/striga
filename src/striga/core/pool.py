
class Pool(object):
#TODO: Active implementation
	'''
Implementation of generic pool.
There are two majon use cases:
1) Pasive pool
	Just keeping resources; pop/return resource is not used

2) Active pool
	Not implemented yet

Start/Stop
Start()
Stop()

	'''

	def __init__(self, min, max, createResourceFnct, deleteResourceFnct):
		self.__CreateResource = createResourceFnct
		self.__DeleteResource = deleteResourceFnct
		self.PoolLowWatermark = min
		self.PoolHighWatermark = max
		self.PoolResources = []
		self.PoolResourcesUID = 1


	def SetLowWatermark(self, value):
		self.PoolLowWatermark = value


	def SetHighWatermark(self, value):
		self.PoolHighWatermark = value


	def Start(self):
		for i in range(self.PoolLowWatermark - len(self.PoolResources)):
			nr = self.__CreateResource(self.PoolResourcesUID)
			self.PoolResources.append(nr)
			self.PoolResourcesUID += 1


	def Stop(self):
		while len(self.PoolResources) > 0:
			r = self.PoolResources.pop()
			self.__DeleteResource(r)
