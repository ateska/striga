from xml.sax.saxutils import quoteattr, escape

###

def _striga_xhtml_escape(text):
	'''Escape text into XHTML'''
	return escape(_striga_xhtml_str(text))

###

def _striga_xhtml_str(text):
	# If you want to improve this, please look at Django smart_srt function
	try:
		return str(text)
	except UnicodeEncodeError:
		return unicode(text).encode('utf-8')

###

def _trailerstrip(name):
	'''
Attribute names are transformed:
	1) to lowercase (based on XHTML specs)
	2) one trailer '_' is removed ... e.g. 'id_' is transformed into 'id'
	3) '__' into '-' (for HTML5 <a data-dismiss> etc.)
	'''

	if len(name) == 0: return name
	if name[-1:] == '_': return name[:-1]
	return name.lower().replace('__','-')

def _striga_xhtml_tag(out, tagname, tagending, params):
	'''
Attributes are handled in following manner:
	1) If attribute value is None or False then its output is suppressed
	2) If attribute value is True then its output transformed into name="name" (e.g. <option selected="selected">)
	3) Other cases of attribute values are handled by printing string representation of given value
	'''
	out.Write(tagname)

	if params is not None:
		for i in range(0, len(params),2):
			v = params[i+1]
			if v is None or v is False: continue
	
			k = _trailerstrip(params[i])
			if v is True:
				out.Write(" {0}={1}".format(k, quoteattr(_striga_xhtml_str(k))))
			else:
				out.Write(" {0}={1}".format(k, quoteattr(_striga_xhtml_str(v))))

	out.Write(tagending)


def _striga_xhtml_tagkw(out, tagname, tagending, params, **kwparams):
	out.Write(tagname)

	if params is not None:
		for i in range(0, len(params),2):
			v = params[i+1]
			if v is None or v is False: continue
	
			k = _trailerstrip(params[i])
			if v is True:
				out.Write(" {0}".format(k))
			else:
				out.Write(" {0}={1}".format(k, quoteattr(_striga_xhtml_str(v))))

	for k, v in kwparams.iteritems():
		if v is None or v is False: continue

		k = _trailerstrip(k)
		if v is True:
			out.Write(" {0}".format(k))
		else:
			out.Write(" {0}={1}".format(k, quoteattr(_striga_xhtml_str(v))))

	
	out.Write(tagending)
