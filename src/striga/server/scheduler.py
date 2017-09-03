import time
import striga.core.prioqueue

###

#TODO: Move scheduler terminology and implementation (when needed) more to following:
#
# class Scheduler 
#	- method At(rel=) - OneShotAbsTimeJob
#	- method At(abs=) - OneShotRelTimeJob
#	- method Every(period=) - PeriodicJob, period can be string with ('1d')
#
#This can be later used even in configuration

###

class Scheduler(striga.core.prioqueue.PriorityQueue):


	def Tick(self):
		nowt = time.time()
		while 1:
			p = self.peek()
			if p is None: break
			if p.Priority <= nowt:
				p = self.get()
				try:
					p()
				finally:
					if hasattr(p, 'Reschedule'):
						p.Reschedule(self)
			else:
				break


	def AddJob(self, job):
		self.put(job, True)


	def RemoveAllJobsFor(self, fnct):
		nqueue = []
		for i in self.queue:
			if i.Fnct == fnct: pass
			nqueue.append(i)

		del self.queue[:]
		for i in nqueue:
			self.AddJob(i)

###

class OneShotAbsTimeJob(striga.core.prioqueue.PriorityContainer):

	def __init__(self, when, fnct, *args, **kwargs):
		striga.core.prioqueue.PriorityContainer.__init__(self, when, fnct, *args, **kwargs)

###

class OneShotRelTimeJob(striga.core.prioqueue.PriorityContainer):

	def __init__(self, when, fnct, *args, **kwargs):
		striga.core.prioqueue.PriorityContainer.__init__(self, time.time() + when, fnct, *args, **kwargs)

###

class PeriodicJob(striga.core.prioqueue.PriorityContainer):


	def __init__(self, period, fnct, *args, **kwargs):
		self.Period = period
		striga.core.prioqueue.PriorityContainer.__init__(self, time.time() + period, fnct, *args, **kwargs)


	def Reschedule(self, scheduler):
		self.Priority = self.Period + time.time()
		scheduler.AddJob(self)
