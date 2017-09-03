import ConfigParser, os, sys
from Tkinter import *

###

class App(Frame):

	def __init__(self, master=None):
		Frame.__init__(self, master)

		config = ConfigParser.ConfigParser()
		config.read(sys.argv[1:])

		self.master = master
		self.Rows = 1
		self.Launchers = []

		sections = config.sections()
		sections.sort()
		for item in sections:
			self.AddRow(master, config, item)

		#Add row with quit button
		qb = Button(master, text="Exit", command=self.ExitProgram).grid(row=self.Rows, column=1, sticky = "s", ipadx = 0, ipady = 0, padx = 2, pady = 4)
		self.rowconfigure(self.Rows, weight=1)

		master.grid_rowconfigure(self.Rows, weight = 1, minsize = 32, pad = 0)
		master.grid_columnconfigure(1, weight = 1, minsize = 455, pad = 0, pad = 10)

		#Self tick ...
		self.Tick()


	def ExitProgram(self):
		sys.exit(0)


	def Tick(self):
		for l in self.Launchers:
			l.Tick()
		self.master.after(500, self.Tick)


	def CleanUp(self):
		for l in self.Launchers:
			l.CleanUp()

		self.Launchers = None


	def AddRow(self, root, config, name):

		ltype = config.get(name,'type')
		if ltype == 'WinService':
			from ._strkick_win32ser import Win32ServiceLauncher
			nl = Win32ServiceLauncher(config.get(name,'name'))
		else:
			from ._strkick_process import Launcher
			startcmd = config.get(name,'startcmd')
			stopcmd = config.get(name,'stopcmd')
			nl = Launcher(startcmd, stopcmd)

		frame = Frame(root,
			borderwidth = 2,
			relief = "groove",
		)
		frame.grid(
			in_	= root,
			column = 1,	row	= self.Rows,
			ipadx = 0, ipady = 0, padx = 0,	pady = 0,
			sticky = "news"
		)

		label_1 = Label(frame,
			text = name[name.index(':')+1:],
		)
		label_1.grid(
			in_	= frame,
			column = 1,	row	= 1,
			ipadx = 0, ipady = 0, padx = 0, pady = 0,
			sticky = "w"
		)


		button_2 = Button(frame,
			text = "Start", command=nl.Start
		)
		button_2.grid(
			in_	= frame,
			column = 2, row	= 1,
			ipadx = 6, ipady = 0, padx = 2, pady = 4,
			sticky = "ew"
		)

		button_3 = Button(frame,
			text = "Stop", command=nl.Stop
		)
		button_3.grid(
			in_	= frame,
			column = 3, row	= 1,
			ipadx = 6, ipady = 0, padx = 2, pady = 4,
			sticky = "ew"
		)

		button_4 = Button(frame,
			text = "Restart", command=nl.Restart
		)
		button_4.grid(
			in_	= frame,
			column = 4, row	= 1,
			ipadx = 0, ipady = 0, padx = 2, pady = 4,
			sticky = "ew"
		)

		button_5 = Button(frame,
			text = "...", command=nl.PrintOutput
		)
		button_5.grid(
			in_	= frame,
			column = 5, row	= 1,
			ipadx = 0, ipady = 0, padx = 2,	pady = 4,
			sticky = "ew"
		)

		# Resize Behavior
		frame.grid_rowconfigure(1, weight = 0, minsize = 10, pad = 0)
		frame.grid_columnconfigure(1, weight = 1, minsize = 2, pad = 0)
		frame.grid_columnconfigure(2, weight = 0, minsize = 10, pad = 10)
		frame.grid_columnconfigure(3, weight = 0, minsize = 10, pad = 10)
		frame.grid_columnconfigure(4, weight = 0, minsize = 10, pad = 10)
		frame.grid_columnconfigure(5, weight = 0, minsize = 10, pad = 5)
		root.grid_rowconfigure(self.Rows, weight = 0, minsize = 16, pad = 0)

		self.Rows += 1

		nl.AssignButtons(button_2, button_3, button_4)
		self.Launchers.append(nl)

###

def Run():

	# create the application
	myapp = App(Tk())

	#
	# here are method calls to the window manager class
	#
	myapp.master.title("Striga Kicker")
	myapp.master.maxsize(1000, 400)

	# start the program
	try:
		myapp.mainloop()
	finally:
		print "Clean up ..."
		myapp.CleanUp()
