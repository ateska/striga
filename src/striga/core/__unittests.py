import unittest
import Queue, logging, logging.handlers, os

import striga.core.executor
import striga.core.variables
import striga.core.prioqueue

####

class TestCase(unittest.TestCase):

	def setUp(self):
		unittest.TestCase.setUp(self)


	def tearDown(self):
		unittest.TestCase.tearDown(self)


############# Test for Executor
	def QtestExecutor(self):
		executor = striga.core.executor.Executor(10)
		executor._StartExecutor()
		self.Counter = 0

		for i in range(10):
			executor.ScheduleWorker(self.__WorkerMethod)

		logging.getLogger('').addHandler(logging.handlers.BufferingHandler(1024))

		try:
			executor.ScheduleWorker(self.__WorkerMethod)
			self.fail('Executor queue should be full')
		except Queue.Full:
			pass

		for i in range(10):
			if not executor.ExecuteWorker(): break

		self.failUnless(self.Counter == 10, "10 in, 10 out")

		executor.ExecuteWorker()
		self.failUnless(self.Counter == 10, "10 in, 10 out")

		executor._StopExecutor()


	def __WorkerMethod(self):
		self.Counter += 1


############# Test for Variables

	def QtestSetVariables(self):
		#Not valid anymore - write a new test
		sv = striga.core.variables.SetVariables()

		sv.POST.v = 1
		sv.POST.v += 1

		self.failUnless(sv.POST.v == 2, 'Dictionary do not contain a tested key')

####

	def testPriorityQueue(self):
		self.PriorityCount = 0

		self.PrioQueue = striga.core.prioqueue.PriorityQueue()
		self.failUnless(self.PrioQueue.peek() is None, "Error in priority queue")

		self.PrioQueue.put(striga.core.prioqueue.PriorityContainer(10, self.__PriorityMethod, 10))
		self.failUnless(self.PrioQueue.peek().Priority == 10, "Error in priority queue")

		self.PrioQueue.put(striga.core.prioqueue.PriorityContainer(9, self.__PriorityMethod, 9))
		self.failUnless(self.PrioQueue.peek().Priority == 9, "Error in priority queue")

		self.PrioQueue.put(striga.core.prioqueue.PriorityContainer(11, self.__PriorityMethod, 11))
		self.failUnless(self.PrioQueue.peek().Priority == 9, "Error in priority queue")

		self.failUnless(self.PriorityCount == 0, "Error in priority queue (call)")

		self.PrioQueue.get()()
		self.failUnless(self.PrioQueue.peek().Priority == 10, "Error in priority queue")

		self.failUnless(self.PriorityCount == 9, "Error in priority queue (call)")

		self.PrioQueue.get()()
		self.failUnless(self.PrioQueue.peek().Priority == 11, "Error in priority queue")

		self.failUnless(self.PriorityCount == 19, "Error in priority queue (call)")

		self.PrioQueue.get()()
		self.failUnless(self.PrioQueue.peek() is None, "Error in priority queue")

		self.failUnless(self.PriorityCount == 30, "Error in priority queue (call)")


	def __PriorityMethod(self, cnt):
		self.PriorityCount += cnt

####

if __name__ == '__main__':
	unittest.main()

