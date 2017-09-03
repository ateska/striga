import sys, time, threading, logging as L
import striga.server.service, striga.core.pool, striga.core.executor

###

class ThreadPoolService(striga.server.service.Service, striga.core.executor.Executor):
#TODO: Spawining more threads when all used

	def __init__(self, parent, name='ThreadPool', startstoppriority = 100):

		striga.server.service.Service.__init__(self, parent, name, startstoppriority)
		striga.core.executor.Executor.__init__(self)

		self.Pool = striga.core.pool.Pool(
			min = 1, max = sys.maxint,
			createResourceFnct = self.__CreateThread,
			deleteResourceFnct = self.__DeleteThread
		)

		self._ChangeServiceStateToConfigured() #Thread pool service is configured by default values


	def GetConfigDefs(self):
		return {'threadpool' : self.__configure }


	def __configure(self, conffilename, min=5, max = sys.maxint, maxqueuesize = 10):
		if self.ServiceState > striga.server.service.Service.States.Configured:
			self.Stop()

		self.Pool.SetLowWatermark(int(min))
		self.Pool.SetHighWatermark(int(max))
		self.SetMaximumWorkerQueueSize(int(maxqueuesize))


	def _DoStart(self):
		self._StartExecutor()
		self.Pool.Start()


	def _DoStop(self):
		for i in range(len(self.Pool.PoolResources)):
			self.ScheduleWorker(None)

		self._StopExecutor()
		self.Pool.Stop()


	def __CreateThread(self, UID):
		if not isinstance(threading.currentThread(), threading._MainThread):
			raise RuntimeError("Worker thread must be launched from MainThread")

		nt = PooledThread(UID, self.ExecuteWorker)
		nt.start()
		return nt


	def __DeleteThread(self, thread):
		thread.Running = False
		thread.join()


###

class PooledThread(threading.Thread):

	def __init__(self, number, executorentry):
		threading.Thread.__init__(self, target = self.Run, name = "PooledThread%d" % number, args=(executorentry,))
		self.Running = True


	def Run(self, executorentry):
		while self.Running:
			if not executorentry():
				break
