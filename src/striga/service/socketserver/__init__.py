import socket, errno, threading, logging
import striga.server.service

L = logging.getLogger('Frontend')

###

class SocketServerService(striga.server.service.Service):
	'''
	Base for socket oriented services
	'''

	BacklogSize = 5 #specifies the maximum number of queued connections and should be at least 1;
					#the maximum value is system-dependent (usually 5).


	def __init__(self, socketreadyfnct, parent, name, startstoppriority):
		striga.server.service.Service.__init__(self, parent, name, startstoppriority)
		self.Socket = None
		self.ListeningThread = threading.Thread(target = self.__run, name = self.GetServiceFullName().replace('.','') + 'Thread',  args=(socketreadyfnct,))
		self._ChangeServiceStateToConfigured()


	def _DoStart(self):
		self._PrepareSocket()
		self.Socket.settimeout(0.5)
		self.Socket.listen(self.BacklogSize)
		self.ListeningThread.start()


	def _DoStop(self):
		self.Socket.close()
		self.ListeningThread.join()
		self.Socket = None


	def _PrepareSocket(self):
		'''
		Override this in implementation
		'''
		pass


	def __run(self, socketreadyfnct):

		while True:
			try:
				sock, addr = self.Socket.accept()

			except socket.timeout:
				continue

			except socket.error, x:
				if x[0] == errno.EBADF:
					# Socket was closed - service is going down
					break

				if x[0] == errno.EAGAIN:
					#"Resource temporarily unavailable": -> Just try again. See http://www.cherrypy.org/ticket/479.
					L.warning("Accept operation on socket returned EAGAIN error (we ignore it)")
					continue

				if x[0] == errno.EINTR:
					#Client disconnected from socket during accept operation ...
					L.warning("Accept operation on socket returned EINTR error (we ignore it)")
					continue

				L.exception("Exception during accepting on the socket (errno = %d)" % x[0])
				raise

			#! TIME CRITICAL !
			socketreadyfnct(sock)

###

class TCPIPv4TCPServerService(SocketServerService):


	def __init__(self, host, port, socketreadyfnct, parent, name, startstoppriority):
		self.Host = host
		self.Port = port
		SocketServerService.__init__(self, socketreadyfnct, parent, name, startstoppriority)


	def _PrepareSocket(self):
		self.Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.Socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.Socket.bind((self.Host, self.Port))
