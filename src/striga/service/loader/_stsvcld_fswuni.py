import striga.server.service

###

class FSWatchdogService(striga.server.service.Service):


    def __init__(self, parent, name='FSWatchdog', startstoppriority = 100):
        striga.server.service.Service.__init__(self, parent, name, startstoppriority)
        self._ChangeServiceStateToConfigured()


    def WatchFile(self, filename, callback):
        pass

###
