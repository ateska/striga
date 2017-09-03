CFLAGS=-Wall -Os

all:	strigapython

strigapython: strigapython.o
	${CC} $^ -o $@

clean:
	rm -f strigapython strigapython.o

install: all
	cp strigapython /usr/local/bin/
