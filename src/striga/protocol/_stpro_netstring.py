import errno, socket, select
import striga.core.exception

__TempErrnos = frozenset([errno.EAGAIN, errno.EWOULDBLOCK, errno.EINPROGRESS])

def RecieveAll(sock, length):
	"""
	Attempts to receive length bytes from a socket, blocking if necessary.
	(Socket may be blocking or non-blocking.)
	"""
	dataList = []
	recvLen = 0
	while length:
		try:
			data = sock.recv(length)
		except socket.error, e:
			if e[0] in __TempErrnos:
				select.select([sock], [], [])
				continue
			else:
				raise
		if not data: # EOF
			break
		dataList.append(data)
		dataLen = len(data)
		recvLen += dataLen
		length -= dataLen
	return ''.join(dataList), recvLen


def ReadNetstring(sock):
	"""
	Attempt to read a netstring from a socket.
	"""
	# First attempt to read the length.
	size = ''
	while True:
		try:
			c = sock.recv(1)
		except socket.error, e:
			if e[0] == errno.EAGAIN:
				select.select([sock], [], [])
				continue
			else:
				raise
		if c == ':':
			break
		if not c:
			raise EOFError
		size += c

	# Try to decode the length.
	try:
		size = int(size)
		if size < 0:
			raise ValueError
	except ValueError:
		raise striga.core.exception.StrigaProtocolError("invalid netstring length")

	# Now read the string.
	s, length = RecieveAll(sock, size)

	if length < size:
		raise EOFError

	# Lastly, the trailer.
	trailer, length = RecieveAll(sock, 1)

	if length < 1:
		raise EOFError

	if trailer != ',':
		raise striga.core.exception.StrigaProtocolError("invalid netstring trailer")

	return s
