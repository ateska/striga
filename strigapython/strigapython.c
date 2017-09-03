#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>

int main(int argc, char ** argv)
{
	char * pythonpath = getenv("STRIGAPYTHON");
	if (pythonpath == NULL)
	{
		fprintf(stderr,"STRIGAPYTHON environment variable is not set!\n");
		exit(1);
	}

	execv(pythonpath, argv);
	fprintf(stderr, "Error launching %s: %s\n", pythonpath, strerror(errno));
	exit(1);
	return 0;
}
