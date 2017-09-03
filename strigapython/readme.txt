TODO ...


CGI
---
ScriptAlias /public/ufoprobe-cgi/ /opt/exiprobes-server-meteonet/cgi/
<Directory /opt/exiprobes-server-meteonet/cgi>
	Order allow,deny
	allow from all

	SetEnv STRIGAPYTHON /usr/bin/python
	Options ExecCGI
</Directory>