#!/usr/bin/env python
import re
import sys


class Event(object):
    _valid_actions = ['drop', 'correlate']

    def __init__(self, event_name, action, logger):

        self.event_name = event_name # Name of the event
        self.action = action # Action taken when such an event is met : correlate/drop/store
        self.logger = logger

        self.regex = ""
        self.named_regex = ""
        self.regex_t = None
        self.labels = []

        self.items_positions = {} # position id to label name. Ex: (0: 'src_ip')
        self.items_capture_positions = {} # same as 'items_positions' without non capturing labels
        self.numberOfLabels = 0

        # We use a custom dict for storing event's item because __dict__ may have conflicts
        self._attr_ = {}

        if not ( self.action in self._valid_actions):
            self.logger.error("Event's action _MUST_ be one of : %s" % str(self._valid_actions))
            sys.exit(1)

        # eof __init__

    def _print(self):
        print "=" * 50
        for key in self._attr_:
            try:
                print "%s = %s" % (key, self._attr_[key])
            except:
                print "ENCODAGE ISSUE = ENCODAGE ISSUE"

        print "=" * 50

    def timestampToRegex(self, timestamp):
        """
        http://docs.python.org/library/datetime.html?highlight=strftime#strftime-strptime-behavior
        """
        reg_t = timestamp

        # before timestamp substitution, espace regex metachars like '+','.', etc
        #reg_t = re.sub('\+', '\\\+', reg_t)
        #reg_t = re.sub('\.', '\\\.', reg_t)
        #reg_t = re.sub('\?', '\\\?', reg_t)

        # use later substitutions
        reg_t = re.sub('%c', '%a %b %d %H:%M:%S %Y', reg_t)
        reg_t = re.sub('%x', '%d/%m/%y', reg_t)
        reg_t = re.sub('%X', '%H:%M:%S', reg_t)

        # substitutions
        reg_t = re.sub('%a', '\w{3}', reg_t)
        reg_t = re.sub('%A', '\w+', reg_t)
        reg_t = re.sub('%b', '\w{3}', reg_t)
        reg_t = re.sub('%B', '\w+', reg_t)
        reg_t = re.sub('%d', '\d{2}', reg_t)
        reg_t = re.sub('%f', '\d{6}', reg_t)
        reg_t = re.sub('%H', '\d{2}', reg_t)
        reg_t = re.sub('%I', '\d{2}', reg_t)
        reg_t = re.sub('%j', '\d{3}', reg_t)
        reg_t = re.sub('%m', '\d{2}', reg_t)
        reg_t = re.sub('%M', '\d{2}', reg_t)
        reg_t = re.sub('%p', '[AP]M', reg_t)
        reg_t = re.sub('%S', '\d{2}', reg_t)
        reg_t = re.sub('%U', '\d{2}', reg_t)
        reg_t = re.sub('%w', '\d', reg_t)
        reg_t = re.sub('%W', '\d{2}', reg_t)
        reg_t = re.sub('%y', '\d{2}', reg_t)
        reg_t = re.sub('%Y', '\d{4}', reg_t)
        reg_t = re.sub('%z', '[\-\+]\d{4}', reg_t)
        #reg_t = re.sub('%Z','', reg_t)
        #reg_t = re.sub('%%','', reg_t)

        return reg_t
        # eof timestampToRegex


    def substituteRegexMacro(self, regex):
        """
        Replace custom's macros like @ipv4 by their regex equivalent.
        Ex: @ipv4 => "\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"
        """
        # timestamp
        ret = re.search(r"@timestamp\[([^\]]+)\]", regex)
        if ret:
            r = self.timestampToRegex(ret.group(1))

            if re.search('%[a-zA-Z]', r):
                self.logger.warning("Timestamp macro conversion probable error (macro=\"%s\", result=\"%s\")" \
                                    % (ret.group(1), r))
            regex = re.sub("@timestamp\[([^\]]+)\]", r, regex)

        # ipv4 (1.22.333.4)
        regex = re.sub("@ipv4", "\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", regex)

        # mac address (AA:AA:AA:AA:AA:AA))
        regex = re.sub("@macAddr",
                       "[a-fA-F0-9]{2}:[a-fA-F0-9]{2}:[a-fA-F0-9]{2}:[a-fA-F0-9]{2}:[a-fA-F0-9]{2}:[a-fA-F0-9]{2}",
                       regex)

        return regex

        # eof substituteRegexMacro()

    def addItem(self, name, value):

        if name in self._attr_:
            self.logger.error("item's name already used in event %s. It _MUST_ be unique." % self.event_name)
            sys.exit(1)

        self._attr_[name] = None

        # evaluate regex's macros
        reg_value = self.substituteRegexMacro(value)

        self.regex += reg_value
        self.labels.append(name) # labels list, just in case

        self.items_positions[self.numberOfLabels] = name
        if re.search('\(', reg_value):
            self.items_capture_positions[len(self.items_capture_positions)] = name

        self.numberOfLabels += 1

    def finalize(self):
        #print self.regex
        self.regex_t = re.compile(self.regex)

        # eof finalize()

    def match(self, rawlog):

        ret = self.regex_t.search(rawlog)

        if ret:
            for i, l in enumerate(ret.groups()):
                self._attr_[self.items_capture_positions[i]] = l
            return self
        return None
        # eof match()

