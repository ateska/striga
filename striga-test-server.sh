#!/bin/sh

exec ${STRIGAPYTHON} ${STRIGAROOT}/striga-server.py -c `dirname $0`/striga-test-server.conf %@
