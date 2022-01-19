global logFileLocation
from time import localtime


def CreateLogFile(filePath=''):
    """ Creates a file to store logged information at the start of a session. """
    global logFileLocation
    t = localtime()
    fileName = '{}-{:02d}-{:02d}--{:02d}.{:02d}.{:02d}.txt'.format(
        t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)
    logFileLocation = filePath + fileName
    with open(logFileLocation, "w+") as f:
        f.close()  # TODO Check; probably more efficient way to do this.


def Log(string_):
    """ Logs given information in the log file during a session. """
    global logFileLocation
    t = localtime()
    timeString = '[{:02d}:{:02d}:{:02d}] '.format(t.tm_hour, t.tm_min,
                                                  t.tm_sec)
    try:
        with open(logFileLocation, "a") as f:
            f.write(timeString + string_ + "\n")
            f.close()
    except:
        pass


def TimeFunction(func):
    """ A decorator that can be used to time functions for efficiency-checking
        purposes."""
    from time import time as CurrentTime

    def wrapper(*args, **kwargs):
        t = CurrentTime()
        to_return = func(*args, **kwargs)
        print(func.__name__, CurrentTime() - t)
        return to_return

    return wrapper