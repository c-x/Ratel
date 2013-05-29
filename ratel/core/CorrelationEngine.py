#!/usr/bin/env python
import re
import sys
import os
import xml.dom.minidom

from ratel.functions import *

class CorrelationRule(object):

    FunctionsEntryPoints = {}
    available_functions  = []

    def __init__(self, name, type, logger, parsers, condition, action, stopRule):
        self.name         = name  # name of the rule
        self.type         = type  # base, window, etc
        self.parsers_list = parsers   # [p1, p2, ..]
        self.condition    = re.sub('\s+', ' ', condition) # (A or B ..)
        self.action       = action   # sendmail
        self.stopRule     = stopRule # True/False
        self.logger       = logger   # log file fd

        # List of functions used by the current condition by position (a smae function can be used mutliple times)
        # used_functions[ contains\(...\) ] = {0: {0:arg1, 1:arg2,}, 1: ..}
        self.used_functions = {}
        self.used_attributes = [] # List of all object's attributes used


        # Load available functions and their entry points (ratel.functions.xxxx)
        functions_module = sys.modules['ratel.functions']
        for func_name in functions_module.__all__:
            if( func_name == "__init__" ):
                continue

            # a "main" _must_ be declared in each functions
            module_name = sys.modules['ratel.functions.%s' % func_name]
            self.available_functions.append( module_name._signature )
            func_call = getattr(module_name, 'main')

            self.FunctionsEntryPoints[ func_name ] = func_call

            # print "func_name   = %s" % func_name
            # print "module_name = %s" % module_name
            # print "sig         = %s" % module_name._signature
            # print "func_call   = %s" % func_call
    # eof __init__()

    def condition_is_valid(self):
        """
        Remove every allowed functions from the condition.
        At the end, if it remains something, that's an error :)
        """
        cond = self.condition.lower()
        cond = re.sub('\s+', ' ', cond)

        for ap in self.available_functions:
            ap = ap.lower()

            ret = re.search(ap, cond)
            if( ret ):
                # [('a', 'b'), ('a', 'b'), ...]
                self.used_functions [ ap ] = re.findall(ap, cond)
                cond = re.sub(ap, ' ', cond)

        # print self.used_functions
        for op in ['and', 'or', 'not']:
            cond = re.sub('\s%s\s' % op, ' ', cond)

        cond = re.sub('\(', '', cond)
        cond = re.sub('\)', '', cond)
        cond = re.sub('\s+', '', cond)

        return ( len(cond) == 0 )

    def evaluate(self, obj):
        """
        Evaluate the provided object to the condition
        """
        #obj._print()

        # substitute event's attributes names by their values.
        cond = self.condition
        for attr in obj._attr_:
            cond = re.sub('evt\.%s' % attr, "\"%s\"" % str(obj._attr_[attr]), cond)

        # if it remains evt.* objects in the rule, there is a problem
        # FIXME: false positive is possible when parsing an url for example containing somethingevt.gif <= 'evt.'
        if( re.search(r'evt\.', cond) ):
            msg  = "Correlation rule (%s) not properly translated. " % self.name
            msg += "Please fix the correlation rule and/or parser! Unexpected: %s" % cond
            self.logger.error(msg)
            return False

        # condition_rule = "(f1(1,3) and f1(2,10)) and f2(5)"
        # eval(condition_rule, {'f1':fct1, 'f2':fct2})
        try:
            res = eval(cond, self.FunctionsEntryPoints)
        except:
            res = False
        return res

    def take_action(self, obj):
        """
        Execute the action of a rule. This mainly execute a script.
        We should add parameters passing ;)
        """
        self.logger.info("Rule \"%s\" triggered and now I'm supposed to run the action \"%s\" with the log's object..." %
                (self.name, self.action) )


class CorrelationEngine(object):

    def __init__(self, config_dir, logger):

        self.numberOfRules = 0
        self._Rules = {} # Order is important for stop conditions : {0: CorrelationRule()}
        self.logger = logger

        self._readXML(config_dir)
    # eof __init__

    def _readXML(self, config_dir):

        # get all xml files from rules directory
        directory = "%s/rules/" % config_dir
        directory = re.sub('//', '/', directory)

        rules_files = []
        for fname in os.listdir( directory ):

            if( re.search('\.xml$', fname.lower()) ):
                f = "%s/%s" % (directory, fname)
                f = re.sub('//', '/', f)

                rules_files.append( f )

        # load each rule file
        for rf in rules_files:
            self.logger.info("Loading rule file %s" % rf)

            XMLFile = xml.dom.minidom.parse( rf )
            for rule in XMLFile.documentElement.getElementsByTagName("rule"):
                r_type = rule.attributes['type'].nodeValue.lower()
                r_name = rule.attributes['name'].nodeValue.lower()

                if( rule.getElementsByTagName("enabled")[0].childNodes[0].nodeValue.lower() != "true" ):
                    self.logger.info("Skipping deactivated rule \"%s\" " % r_name)
                    continue

                stopRule = True
                if( rule.getElementsByTagName("stopRule")[0].childNodes[0].nodeValue.lower() != "true" ):
                    stopRule = False

                self.logger.info("Load rule \"%s\" (stop=%s)" % (r_name, stopRule))
                parsers_list = []
                for item in rule.getElementsByTagName("parser"):
                    p = item.childNodes[0].nodeValue
                    if( not (p in parsers_list) ):
                        parsers_list.append( p )

                action    = rule.getElementsByTagName("action")[0].childNodes[0].nodeValue.lower()
                condition = rule.getElementsByTagName("condition")[0].childNodes[0].nodeValue.lower()

                # check *here* that each requested parser exist

                c = CorrelationRule(r_name, r_type, self.logger, parsers_list, condition, action, stopRule)
                if( not c.condition_is_valid() ):
                    self.logger.error("Invalid rule condition for %s (type=%s)" % (r_name,r_type))
                    sys.exit(1)

                self._Rules[ self.numberOfRules ] = c
                self.numberOfRules += 1

    def evaluate(self, parser_name, obj):

        if( obj.action == "drop" ):
            return

        parser_name = re.sub('\.parser$', '', parser_name) # linux/iptables

        for rule_id in self._Rules:
            rule = self._Rules[ rule_id ]

            #print "="*50
            #print "rule_id     = %s" % rule_id
            #print "parser_name = %s" % parser_name
            #print "parser_lsit = %s" % rule.parsers_list

            if( not (parser_name in rule.parsers_list) ):
                continue

            ret = rule.evaluate(obj)
            if( ret ):
                rule.take_action(obj)

            if( rule.stopRule ):
                break;


if( __name__ == "__main__" ):
    from ratel.core.Logger import Logger
    cor = CorrelationEngine("./", Logger('.'))
    #cor.evaluate( obj )

