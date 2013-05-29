#!/usr/bin/env python
import re
import os
import time

import threading
# du multiprocessing ne serait-il pas plus intelligent ?

class File(threading.Thread):
    """
    We'll consider adding checkpoints on next release to resume reading in case of crash (or stop)
    """

    def __init__(self, filename, parsers_list, log_unparsed, logsQueue, logger):
        threading.Thread.__init__(self)

        self.file_pattern = filename
        self.parsers_list = parsers_list
        self._logsQueue = logsQueue
        self.logger = logger

        self.useDate = False
        self.useID = False

        self._date_format = None
        self._idMinValue = 0
        self._idMaxValue = 0
        self._idNumberOfDigits = 0

        self.log_unparsed = ( log_unparsed.lower() == "true" )

        # Do the filename use @id macro ?
        ret = re.search("@id\[([^\]]+)\]", filename)
        if ret:
            r = ret.group(1).split(',')

            self._idMinValue = int(r[0])
            self._idMaxValue = int(r[1]) #+ 1
            self._idNumberOfDigits = int(r[2])
            self.useID = True

        # Do the filename use @timestamp macro ?
        ret = re.search("@timestamp\[([^\]]+)\]", filename)
        if ret:
            self._date_format = ret.group(1)
            self.useDate = True

        # consistancy checks
        if self._idMinValue > self._idMaxValue:
            self._idMinValue = self._idMaxValue
        if self._idNumberOfDigits < 1:
            self._idNumberOfDigits = 0

    # eof __init__

    def identify(self):
        s = "source_type=file, path=%s, parsers=%s" % \
            (self.file_pattern, str(self.parsers_list))
        return s

    # return the next formated id or None if the limit is reached
    # just return if idMaxValue is reached.
    def _getNextID(self, current_id):

        if not self.useID:
            return None

        fmt = "%%0%sd" % self._idNumberOfDigits

        if current_id is None:
            return fmt % self._idMinValue

        i = int(current_id)
        if i >= self._idMaxValue:
            return current_id

        i += 1
        return fmt % i

        # eof _getNextID()

    def makeFilename(self, c_id, c_date):
        filename = self.file_pattern

        if c_id:
            filename = re.sub("@id\[[^\]]+\]", c_id, filename)
        if c_date:
            filename = re.sub("@timestamp\[[^\]]+\]", c_date, filename)

        return filename

    def _getDate(self):
        if not self._date_format:
            return None
        return time.strftime(self._date_format)

    def run(self):

        seek_pos = 0
        current_id = self._getNextID(None)
        current_date = self._getDate()

        while True:
            # 1- Get the current filename according to date/id
            # 2- Read it until EOF
            # 3- Next id if it exist or next date if it exist, else, stay on the same and sleep
            EOF = False
            sleepTime = 30 # When eof is reached, sleep

            filename = self.makeFilename(current_id, current_date)
            try:
                self.logger.info("Working with log file %s (pos = %s)" % (filename, seek_pos))
                fd = open(filename, "r")
                fd.seek(seek_pos)

                line = fd.readline()
                while line:
                    seek_pos = fd.tell()
                    line = line.strip()

                    # push the log line to the stack with it's associated parsers
                    item = {'raw': line, 'parsers': self.parsers_list, 'log_unparsed': self.log_unparsed}
                    self._logsQueue.put(item)

                    line = fd.readline()
                fd.close()
                EOF = True
            except:
                self.logger.error("Failed to open log file %s" % filename)

            # Next file
            if EOF:
                c_id = self._getNextID(current_id)
                c_date = self._getDate()
                next_filename = self.makeFilename(c_id, c_date)

                if (next_filename != filename) and (os.path.isfile(next_filename)):
                    current_id = c_id
                    current_date = c_date
                    filename = next_filename
                    sleepTime = 0
                    seek_pos = 0
            time.sleep(sleepTime)
            # eof run()
