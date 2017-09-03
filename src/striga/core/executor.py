import Queue, logging as L
import striga.core.exception

###

class Executor(object):
	'''
Executor class is implementation of 'deffered execution' pattern.
It is wrapper on Queue object where you can put callables that will be called later
possibly from other thread.

Start/Stop:
	_StartExecutor
	_StopExecutor

Inserting workers (callables):
	ScheduleWorker

Executing workers (if some in the queue):
	ExecuteWorker
	'''

	def __init__(self, maxworkerqueuesize = 10):
		self.__WorkerQueue = None
		self.__MaxWorkerQueueSize = maxworkerqueuesize


	def SetMaximumWorkerQueueSize(self, maxworkerqueuesize):
		self.__MaxWorkerQueueSize = maxworkerqueuesize


	def _StartExecutor(self):
		if self.__WorkerQueue is not None:
			raise striga.core.exception.StrigaRuntimeException("Executor is already started")

		self.__WorkerQueue = Queue.Queue(self.__MaxWorkerQueueSize)


	def _StopExecutor(self):
		if self.__WorkerQueue is None:
			raise striga.core.exception.StrigaRuntimeException("Executor is not started")

		self.__WorkerQueue.join()
		self.__WorkerQueue = None


	def ScheduleWorker(self, *args):
		'''
		First argument is worker (callable), following are arguments for callable
		'''
		#! TIME CRITICAL !

		if self.__WorkerQueue is None:
			raise striga.core.exception.StrigaRuntimeException("Executor is not started")

		#TODO: Measure how long worker stays in queue

		if len(args) < 1:
			raise striga.core.exception.StrigaRuntimeException("You must specify worker as callable (first argument to ScheduleWorker)")

		for i in range(10):
			try:
				self.__WorkerQueue.put(args, True, 1)
				return
			except Queue.Full:
				L.warning("Worker queue full (try #%d)" % i)

		raise Queue.Full("Worker queue is long-time full")


	def ExecuteWorker(self, timeout = 0.5):
		'''
		Check worker queue and if there is a worker, execute that.
		Return False in case when ExecuteWorker should not be called anymore (etc. when application is closing)
		'''
		if self.__WorkerQueue is None:
			raise striga.core.exception.StrigaRuntimeException("Executor is not started")

		try:
			worker = self.__WorkerQueue.get(True, timeout)
		except Queue.Empty:
			return True

		try:
			if worker[0] is None:
				return False

			try:
				worker[0](*worker[1:])

			except SystemExit, e:
				L.info("System exiting with exit code %s", e)
				raise

			except striga.core.exception.StrigaFatalError, e:
				L.critical("Fatal exception in worker - terminating ...")
				raise

			except:
				L.exception("Expection in worker execution")

		finally:
			self.__WorkerQueue.task_done()

		return True


	def _DiscardAllPendingWorkers(self):
		'''
		Usable when executor is finishing its activity without completing all workers in the queue (premature exits)
		'''

		try:
			while 1:
				self.__WorkerQueue.get_nowait()
				self.__WorkerQueue.task_done()
		except Queue.Empty:
			pass
