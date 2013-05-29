#!/usr/bin/env python
import re
import sys
import xml.dom.minidom

from Event import Event


class Parser(object):
    """
    1 Parser = 1 log format/type = X events = X regex

    a Parser is something between a log line and an object representation of that log line :
    Parser(log ligne) => Object
    """

    def _readXML(self, filename):
        try:
            self.logger.info("Loading events from parser %s" % filename)
            XMLFile = xml.dom.minidom.parse(filename)

            for event in XMLFile.documentElement.getElementsByTagName("event"):
                e_name = event.attributes['name'].nodeValue
                e_action = event.attributes['action'].nodeValue

                evt = Event(e_name, e_action, self.logger)
                self.logger.info("Added a new event with name %s and action %s" % (e_name, e_action))

                for item in event.getElementsByTagName("item"):
                    label = item.attributes['label'].nodeValue
                    regex = item.childNodes[0].nodeValue

                    evt.addItem(label, regex)
                    self.logger.info(" -> Event %s : new item added (%s)" % (e_name, label))
                evt.finalize()
                self.events.append(evt)
        except Exception, e:
            self.logger.error("Can't parse the parser file \"%s\" (%s)" % (filename, str(e)))
            sys.exit(1)

        # eof _readXML

    def __init__(self, config_dir, parser_name, logger):
        # linux/iptables.parser => linux/iptables
        self.parser_name = re.sub('\.parser$', '', parser_name)
        self.logger = logger
        self.events = []

        parser_path = "%s/parsers/%s" % (config_dir, parser_name)
        parser_path = re.sub("//", "/", parser_path)

        self._readXML(parser_path)

        # eof __init__

    def parse(self, rawlog):

        # events _MUST_ be ordered for efficiency
        for evt in self.events:
            ret = evt.match(rawlog)
            if ret:
                return ret
        return None
        # eof parse()

