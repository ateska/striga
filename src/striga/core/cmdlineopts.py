import optparse

class CommandLineOptions(object):

	def __init__(self, optionlist, defaults):
		optparser = optparse.OptionParser(option_list=optionlist)
		optparser.set_defaults(**defaults)
		options, self.Args = optparser.parse_args()

		for item in options.__dict__.iteritems():
			setattr(self, item[0], item[1])

