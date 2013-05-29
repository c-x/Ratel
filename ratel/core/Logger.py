#!/usr/bin/env python

import re
import sys
import time

class Logger:

    def __init__(self, config_dir):
        self.fs = sys.stdout
        self.useDate = False
        self.file_pattern = ""

        try:
            self.file_pattern = re.sub('//', '/', config_dir + "/logs/ratel-%Y.%m.%d.log")

            fname = time.strftime( self.file_pattern )

            if fname != self.file_pattern:
                self.useDate = True

            self.fs = open(fname, "a")
            self.info("RATEL START   \_o<   \_o<")
        except Exception, e:
            print "FAILED to open log file : %s" % str(e)
            sys.exit(1)
    # eof __init__

    def _reopen(self):

        if not self.useDate:
            return
        try:
            fname = time.strftime(self.file_pattern)
            self.fs = open(fname, "a")
        except Exception, e:
            print "FAILED to re-open the log file : %s" % str(e)
            sys.exit(1)

    def _write(self, level, msg):
        self._reopen()
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.fs.write("[%s] %s: %s\n" % (timestamp, level, msg.strip()) )

    def info(self, msg):
        self._write('INFO', msg)

    def warn(self, msg):
        self._write('WARNING', msg)

    def error(self, msg):
        self._write('ERROR', msg)

    def debug(self, msg):
        self._write('DEBUG', msg)

    def uevent(self, msg):
        self._write('UEVENT', msg)

