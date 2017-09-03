import win32serviceutil

###

class Win32ServiceLauncher(object):


	def __init__(self, servicename):
		self.ServiceName = servicename
		self.Machine = ''


	def AssignButtons(self, startbtn, stopbtn, restartbnt):
		self.StartBtn = startbtn
		self.StopBtn = stopbtn
		self.RestartBtn = restartbnt


	def CleanUp(self):
		pass


	def Tick(self):
		status = win32serviceutil.QueryServiceStatus(self.ServiceName, self.Machine)[1]
		if status == 4:
			self.StartBtn.configure(state = "disabled")
			self.StopBtn.configure(state = "normal")
			self.RestartBtn.configure(state = "normal")
		elif status == 1:
			self.StartBtn.configure(state = "normal")
			self.StopBtn.configure(state = "disabled")
			self.RestartBtn.configure(state = "disabled")
		else:
			self.StartBtn.configure(state = "disabled")
			self.StopBtn.configure(state = "disabled")
			self.RestartBtn.configure(state = "disabled")


	def Start(self):
		win32serviceutil.StartService(self.ServiceName, self.Machine)


	def Stop(self):
		win32serviceutil.StopService(self.ServiceName, self.Machine)


	def Restart(self):
		win32serviceutil.RestartService(self.ServiceName, self.Machine)


	def PrintOutput(self):
		print "===="
		print win32serviceutil.QueryServiceStatus(self.ServiceName, self.Machine)
		print "===="
