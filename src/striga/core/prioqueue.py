# From discussion at http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/87369
from Queue import Queue
from heapq import heappush, heappop

###

class PriorityQueue(Queue):
	# Initialize the queue representation
	def _init(self, maxsize):
		self.maxsize = maxsize
		self.queue = []

	# Put a new item in the queue
	def _put(self, item):
		return heappush(self.queue, item)

	# Get an item from the queue
	def _get(self):
		return heappop(self.queue)


	def peek(self):
		if len(self.queue) == 0: return None
		return self.queue[0]

###

class PriorityContainer(object):


	def __init__(self, priority, fnct, *args, **kwargs):
		self.Priority = priority
		self.Fnct = fnct
		self.Args = args
		self.KWArgs = kwargs


	def __call__(self):
		return self.Fnct(*self.Args, **self.KWArgs)


	def __le__(self, b):
		#For heapq
		return self.Priority <= b.Priority

