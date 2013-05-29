#!/usr/bin/env python
import re
import sys
import os

from Queue import Queue

from ratel.core.Source import Source
from ratel.core.Logger import Logger
from ratel.core.Parser import Parser
from ratel.core.CorrelationEngine import CorrelationEngine


import threading
class ParserWorker(threading.Thread):

    _Parsers     = []
    parsers_list = []
    _logsQueue   = None
    _objsQueue   = None
    logger       = None

    _ParsersByName = {}

    def __init__(self, config_dir, parsers_list, logsQueue, ObjectsQueue, logger):
        threading.Thread.__init__(self)

        self.config_dir = config_dir
        self.logger     = logger
        self._logsQueue = logsQueue
        self._objsQueue = ObjectsQueue
        self.parsers_list = parsers_list

        # load parsers
        self._ParsersByName = {}
        for p in parsers_list:
            self._ParsersByName[ p ] = Parser(config_dir, p, logger)

    # eof __init__

    def run(self):
        logger.info("Parsers worker ready.")

        while( True ):

            item = self._logsQueue.get()

            # trying to parse the raw log
            for p in item['parsers']:
                o = self._ParsersByName[p].parse(item['raw'])
                if( o ):
                    #push the object to the correlation stack
                    #self._objsQueue.put( o )
                    self._objsQueue.put( {'parser': p, 'obj' : o} )
                    break

            # if parsing failed, log the raw log line
            if( (not o) and item['log_unparsed'] ):
                m = "parsers=%s rawlog=%s" % (str(item['parsers']), item['raw'])
                logger.uevent(m)

            self._logsQueue.task_done()
# eof ParserWorker


class CorrelationWorker(threading.Thread):

    logger = None
    queue  = None

    def __init__(self, config_dir, queue, logger):
        threading.Thread.__init__(self)

        self.logger = logger
        self.queue  = queue

        # load correlation rules here :)
        self.corEngine = CorrelationEngine(config_dir, logger)

    def run(self):

        while( True ):
            item = self.queue.get()
            self.corEngine.evaluate( item['parser'], item['obj'] )
            self.queue.task_done()

def usage(pname):
    print ""
    print "%s -c /path/to/root/directory" % pname
    print "Ex:"
    print "%s -c /home/ratel"
    print ""
    sys.exit(1)


if( (__name__ != "__main__") or (len(sys.argv) != 3) ):
    usage(sys.argv[0])


# option parsing & init
config_dir = sys.argv[2]


logger       = Logger(config_dir)
LogsQueue    = Queue(0) # stack where to put raw logs and associated parsers
ObjectsQueue = Queue(0) # stack where to put objects represention of logs


print "[+] Loading sources..."
TrackedSources = Source(config_dir, LogsQueue, logger)
print "[+] Loading parsers..."
needed_parsers = TrackedSources.getAllRequiredParsersList()

# launching parsing workers :
# get a rawlog from the logsQueue and transform that rawlog into an object
# and put it in the objectsQueue.
# note : every worker load all parsers
workers_list = []
for i in range(0, (len(needed_parsers) * 2)):
    print "[+] Lauching a worker (parser thread)..."
    logger.info("Launching a parser thread (%s)" % i)

    w = ParserWorker(config_dir, needed_parsers, LogsQueue, ObjectsQueue, logger)
    w.start()
    workers_list.append( w )

# lauching correlation worker
# Getting objects from objectsQueue.
print "[+] Lauching correlation engine..."
w = CorrelationWorker(config_dir, ObjectsQueue, logger)
w.start()

# start reading sources
print "[+] Starting to read files sources..."
TrackedSources.start()

print "[+] Now, everything will happend in background and in log files, see logs directory in %s" % config_dir



