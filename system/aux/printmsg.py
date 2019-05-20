import sys

def begin(message):
    """
    Print message to show that a process has been initiated.

    args:
        message - the message to be printed
    """
    sys.stdout.write('\n')
    sys.stdout.write('\033[F') # cursur up
    sys.stdout.write('\033[K') # erase line
    sys.stdout.write(message + '...')
    sys.stdout.flush()


def end():
    """
    Print 'Done' to show that a process has been finished.
    """
    sys.stdout.write('Done\n')
    sys.stdout.flush()