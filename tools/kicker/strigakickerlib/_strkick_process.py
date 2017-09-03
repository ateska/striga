import subprocess, threading, sys, os, time

###

class Launcher(object):


	def __init__(self, startcmd, stopcmd):
		self.StartCmd = startcmd
		self.StopCmd =  stopcmd
		self.SubProcess = None
		self.Output = []


	def CleanUp(self):
		self.Stop()


	def AssignButtons(self, startbtn, stopbtn, restartbnt):
		self.StartBtn = startbtn
		self.StopBtn = stopbtn
		self.RestartBtn = restartbnt


	def IsStarted(self):
		if self.SubProcess is None: return False
		if self.SubProcess.poll() is None: return True

		#Perform cleaning
		self.SubProcess.wait()
		self.SubProcess = None

		return False


	def Tick(self):

		#Check status ...
		if self.IsStarted():
			self.StartBtn.configure(state = "disabled")
			self.StopBtn.configure(state = "normal")
			self.RestartBtn.configure(state = "normal")
		else:
			self.StartBtn.configure(state = "normal")
			self.StopBtn.configure(state = "disabled")
			self.RestartBtn.configure(state = "disabled")


	def Start(self):
		if sys.platform == "win32":
			kwargs = {}
		else:
			kwargs = {'close_fds':True}

		print "Starting process", self.StartCmd
		self.SubProcess = subprocess.Popen(self.StartCmd, shell=True, bufsize=0, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs)

		self.Output = []
		t = threading.Thread(target=self._readerthread, args=('E', self.SubProcess.stderr))
		t.setDaemon(True)
		t.start()

		t = threading.Thread(target=self._readerthread, args=('O', self.SubProcess.stdout))
		t.setDaemon(True)
		t.start()


	def Stop(self):
		if self.SubProcess is None: return

		print "Stopping process", self.StopCmd

		if self.StopCmd == 'KILL':
			if sys.platform == "win32":
				os.popen('taskkill /PID '+str(self.SubProcess.pid)+' /F /T')
			else:
				print 'kill ' + str(self.SubProcess.pid)
				os.popen('kill ' + str(self.SubProcess.pid))
		else:
			os.popen(self.StopCmd)

		self.SubProcess.wait()
		self.SubProcess = None


	def Restart(self):
		self.Stop()
		self.Start()


	def PrintOutput(self):
		print "====="
		for s,l in self.Output:
			print l
		print "====="


	def _readerthread(self, stype, handle):
		try:
			while self.SubProcess is not None:
				buffer = handle.read()
				if len(buffer) == 0:
					time.sleep(0.5)
					continue
				self.Output.append((stype, buffer))
		except:
			print "!!!!! Exception in reader thread"
