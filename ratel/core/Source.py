#!/usr/bin/env python

import re
import sys
import xml.dom.minidom

import threading

from File import File


class Source(threading.Thread):
    def __init__(self, config_dir, logsQueue, logger):
        threading.Thread.__init__(self)
        self._logsQueue = logsQueue
        self.logger = logger

        # List of tracked files and associated parsers
        self.watchlist_files = {} # ['filename-path'] = [parser1, parser2, ..]
        self._Sources = []

        self._readXML(config_dir)

        # eof init

    def run(self):
        for s in self._Sources:
            self.logger.info("Starting monitoring on %s" % s.identify())
            s.start()

    def getAllRequiredParsersList(self):
        """
        Return a list of parsers ['p1', 'p2', ...]
        """
        ret = []
        for f in self.watchlist_files:
            for p in self.watchlist_files[f]:
                if not p in ret:
                    ret.append(p)
        return ret

    def _readXML(self, config_dir):
        try:
            filename = re.sub('//', '/', "%s/sources/sources.xml" % config_dir)
            self.logger.info("Loading sources from %s" % filename)
            XMLFile = xml.dom.minidom.parse(filename)

            for source in XMLFile.documentElement.getElementsByTagName("source"):
                s_type = source.attributes['type'].nodeValue.lower()
                log_unparsed = source.attributes['log_unparsed'].nodeValue.lower()

                if s_type == "file":
                    for path in source.getElementsByTagName("path"):
                        f = path.childNodes[0].nodeValue

                        if f in self.watchlist_files:
                            self.logger.error("Duplicate source : %s" % f)
                            sys.exit(1)

                        self.logger.info("Adding file %s to watch list" % f)
                        self.watchlist_files[f] = []

                        for parser in source.getElementsByTagName("parser"):
                            self.watchlist_files[f].append(parser.childNodes[0].nodeValue)

                        fi = File(f, self.watchlist_files[f], log_unparsed,
                                  self._logsQueue, self.logger)
                        self._Sources.append(fi)
                elif s_type == "wmi":
                    self.logger.warning("Collecting WMI from Linux is cool ! - not yet implemented.")
                else:
                    self.logger.warning("We've got plans for SSH, SQL, CIFS, FTP, "
                                        "HTTP, etc, but it's not implemented yet.")
        except Exception, e:
            self.logger.error("Can't parse the parser file \"%s\" (%s)" % (filename, str(e)))
            sys.exit(1)
            # eof _readXML
