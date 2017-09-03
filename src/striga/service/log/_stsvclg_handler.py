import os, logging, datetime

###

class ManagedRotatingFileHandler(logging.FileHandler):
	"""
	Handler for logging to a file, rotating the log file at signal from main process.

	If backupCount is > 0, when rollover is done, no more than backupCount
	files are kept - the oldest ones are deleted.
	"""
	def __init__(self, filename, rotateWhen, interval, backupCount=0, encoding=None):
		logging.FileHandler.__init__(self, filename, 'a', encoding, delay = 0)
		self.backupCount = backupCount

		self.interval = interval
		today = datetime.date.today()
		self.rotateAt = datetime.datetime(year = today.year, month = today.month, day = today.day, hour = rotateWhen.hour, minute = rotateWhen.minute, second = rotateWhen.second, microsecond = rotateWhen.microsecond)

		self.FindNewRolloverDate()


	def FindNewRolloverDate(self):
		while self.rotateAt < datetime.datetime.now():
			self.rotateAt += self.interval


	def CheckRollover(self, curtime):
		if self.rotateAt > curtime: return
		self.FindNewRolloverDate()

		logging.debug("Rotating log file '%s'", self.baseFilename)
		self.acquire()
		try:
			self._DoRollover()
		finally:
			self.release()
		logging.info("Log file '%s' rotated", self.baseFilename)


	def _DoRollover(self):
		#TODO: Improve error handling
		self.stream.close()

		if self.backupCount > 0:
			for i in range(self.backupCount - 1, 0, -1):
				sfn = "%s.%d" % (self.baseFilename, i)
				dfn = "%s.%d" % (self.baseFilename, i + 1)
				if os.path.exists(sfn):
					if os.path.exists(dfn):
						os.remove(dfn)
					os.rename(sfn, dfn)
			dfn = self.baseFilename + ".1"
			if os.path.exists(dfn):
				os.remove(dfn)
			os.rename(self.baseFilename, dfn)

		self.mode = 'w'
		self.stream = self._open()

