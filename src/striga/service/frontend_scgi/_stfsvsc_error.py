import traceback
from xml.sax.saxutils import escape

import striga

###
#Based on http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/52215 from Bryn Keller
###

#TODO: Based on security settings send only partial information (no version)
StrigaVersion = 'Striga Server %s' % striga.Version

###

def SendErrorPage(socket, exctype, value, tb):

	econtent = '''<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2//EN">
<html>
	<head>
		<title>Striga - Error during context preparation</title>
		<STYLE type="text/css">
li.olli {
	margin: 0 0 1em 0;
}
		</STYLE>
	</head>
	<body>

<h1>Error during context preparation</h1>

<h2>Exception</h2>
<code>'''  + '<br>'.join([escape(x) for x in traceback.format_exception_only(exctype, value)]) + '''</code>

<h2>Traceback</h2>
<ol>'''

	frameno = 0
	for fname, lineno, fnname, text in traceback.extract_tb(tb):
		frameno += 1
		econtent += '<li class="olli"><strong><code>' + escape(text) + '</code></strong><br>'
		econtent += 'File ' + escape(fname) + ' at line %d<br>' % lineno
		econtent += ('Function <a href="#frame%d">' % frameno) + escape(fnname) + '</a></li>'

	econtent += '''
</ol>
<h2>Locals by frame</h2>
<ol>
'''

	stack = []
	while tb:
		stack.append(tb.tb_frame)
		tb = tb.tb_next

	frameno = 0
	for frame in stack:
		frameno += 1
		econtent += '<li class="olli"><a name="frame%d">' % frameno + escape("Frame %s in %s at line %s" % (frame.f_code.co_name,
											 frame.f_code.co_filename,
											 frame.f_lineno)) + '</a>'

		if len(frame.f_locals) > 0:
			econtent += '<ul>'
			for key, value in frame.f_locals.items():
				econtent += "<li><code>" + escape("%20s = " % key)
				#We have to be careful not to cause a new error in our error
				#printer! Calling str() on an unknown object could cause an
				#error we don't want.
				try:
					econtent += escape(str(value))
				except:
					econtent += escape("<ERROR WHILE PRINTING VALUE>")
				econtent += '</code></li>'

			econtent += '</ul>'
		econtent += '</li>'

	econtent += '''</ol><hr>
''' + StrigaVersion + '''
	</body>
</html>'''

	socket.send('\r\n'.join([
'Status: 500 Internal Server Error',
'X-Powered-By: ' + StrigaVersion,
'Content-Length: %d' % len(econtent),
'Content-Type: text/html',
'',
'',
]) + econtent)
