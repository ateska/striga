import threading

class MRSWLock(object):
	"Multi-read single-write lock object"

	def __init__(self):
		# critical-section lock & the data it protects
		self.__rwOK = threading.Lock()
		self.__nr = 0  # number readers actively reading (not just waiting)
		self.__nw = 0  # number writers either waiting to write or writing
		self.__writing = 0  # 1 iff some thread is writing

		# conditions
		self.__readOK  = threading.Condition(self.__rwOK)  # OK to unblock readers
		self.__writeOK = threading.Condition(self.__rwOK)  # OK to unblock writers


	def ReadIn(self):
		self.__rwOK.acquire()
		while self.__nw:
			self.__readOK.wait()
		self.__nr = self.__nr + 1
		self.__rwOK.release()


	def ReadOut(self):
		self.__rwOK.acquire()
		if self.__nr <= 0:
			raise ValueError, '.ReadOut() invoked without an active reader'
		self.__nr = self.__nr - 1
		if self.__nr == 0:
			self.__writeOK.notify()
		self.__rwOK.release()


	def WriteIn(self):
		self.__rwOK.acquire()
		self.__nw = self.__nw + 1
		while self.__writing or self.__nr:
			self.__writeOK.wait()
		self.__writing = 1
		self.__rwOK.release()


	def WriteOut(self):
		self.__rwOK.acquire()
		if not self.__writing:
			raise ValueError, '.WriteOut() invoked without an active writer'
		self.__writing = 0
		self.__nw = self.__nw - 1
		if self.__nw:
			self.__writeOK.notify()
		else:
			self.__readOK.notifyAll()
		self.__rwOK.release()


	def WriteToRead(self):
		self.__rwOK.acquire()
		if not self.__writing:
			raise ValueError, '.WriteToRead() invoked without an active writer'
		self.__writing = 0
		self.__nw = self.__nw - 1
		self.__nr = self.__nr + 1
		if not self.__nw:
			self.__readOK.notifyAll()
		self.__rwOK.release()


	def Acquire(self):
		return self.WriteIn()


	def Release(self):
		return self.WriteOut()
