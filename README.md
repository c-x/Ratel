# Ratel (PoC) v0.1

##### Join !
* IRC Channel: irc.freenode.net ( #ratel )
* Author's twitter: @_CLX

##### Ratel was wrote :
* as a PoC to demonstrate some ideas I've in mind (log management, correlation).
* in a 5 days hardcoding session (hell, this is a PoC, don't be too much crude!)

If I've some feedback from _YOU_, I will start the development of "real"
version, in C/C++ for efficiecy (Python is cool, but slooowww...).

##### In few words, Ratel goals are:
* To become a correlation framework
* To let users write rules based on boolean expressions
* To let users write their own functions for the correlation part
* Maybe build a 'SIEM/SIM/SEM' community, who knows...

##### Ratel is a PoC :
Ratel is a PoC which means that's a simple demonstrator and not all functionnalities are coded. For example,
the correlation currently working is only 'base rules' ('windows' and 'counter' rules are not yet implemented).

If you find any interest to this kind of software, **SEND ME YOUR FEEDBACK/ADVICE/COMMENT**. I will then engage the
development of a real version.

So, it's up to you ;-)



### Why this code ?
Because I think we need it. I don't know any other open source software like
this one. Moreover, I've seen commercial softwares, and expensives one, which
simply _do not work_.


### What's next ?
If I've enough feedback, I will start the development of a real version,
which will include distributed architecture capabilities, reporting, etc. I 
think I will need help !


### Ratel ?
I will let you get informed with wikipedia and other sites/books, but in short,
a ratel is a little omnivorus and nasty animal. Ratels also enjoy honey !


### Feedback ?
I need YOUR feedback. Test this code, send me uses cases, logs, rules, bugs,
etc.  What features do you want to see in such a framework ?

### Documentation ?
Yes ... read this README completely, read the comments into configuration files
and finally, read the code :-P.


### Process flow ?
In short: flat log file -> File Tracker -> Parser -> Correlator -> Alerts

For now this code only read flat local files. In next release, some connectors
will be added : SQL, WMI, HTTP, FTP, etc.


### Performances ?
Well, on my little laptop (Core 2 duo, 2Ghz, 3GB Ram), I was able to parse a 
270MB file in 35 secondes.  The log file had lines around 400 bytes each and the
associated parser was composed of 19 fields (see bluecoat/http).

Saying that, that's not impressive... but, hey, that's a PoC ! Moreover a PoC in
Python !  So yes, that's damn slooowwww (although it may satisfied some users).

### Log severity
Ratel has generic log severity plus the 'uvent' one : 
* INFO : Generic information
* WARN : Warning, unexpected behavior but non blocking for Ratel 
* ERROR: Error, blocking event for Ratel 
* DEBUG: You won't see this in production environments
* UEVENT: Unkwown Event, related to a not completed parser.


### What are macros ?
Macros are just shortcuts for regex. For now there are only few :
* @timestamp[] => `see python/php strftime() for help`
* @macAddr[]   =>
  `[a-fA-F0-9]{2}:[a-fA-F0-9]{2}:[a-fA-F0-9]{2}:[a-fA-F0-9]{2}:[a-fA-F0-9]{2}:[a-fA-F0-9]{2}`
* @ipv4        => `\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}`


### Setup ?
##### 1. Get the code Clone the code from this github where you want on your system.
```bash
$ cd /home 
$ git clone https://github.com/c-x/Ratel 
```

##### 2. Centralise your log files using syslog-ng or whatever method you like/need.
Ratel need flat log files and it's a good idea to centralize them all into a
directory (say /logs) and name them according to hostnames and rotate files
based on date/time (see syslog-ng macros).

Ratel can also follow files which are rotated with a number (like
/var/log/messages.1, .2, ..).

Ratel follow files in real time so each line is read only once. When Ratel reach
the end of the file, it wait until the next file appears or new lines comes in
the current files (like 'tail -f').

##### 3. You've got logs, now prepare regex to describes log lines 
Before triggering alerts, it's better to know what kind of logs you have. To 
achieve that, Ratel require that you create parsers for each log files you 
have.

So, parsers must be written in the 'parsers' directory. Each parser must have
it's own directory. For example, if you want to parse apache, or squid, or
wathever, create a meaningful directory into the parsers directory :
<pre>
  ~/parsers/apache 
  ~/parsers/squid 
  ~/parsers/juniper 
  ~/parsers/cisco
</pre>

In each directory, you may have one or more parser file. A parser file is a
collection of regex and is named 'parser_name.parser'.  For example, for Cisco,
you may wants an Cisco ASA parser and a Switch/Router parser :
<pre>
  ~/parsers/cisco/asa.parser 
  ~/parsers/cisco/router.parser
</pre>

Those parser will be used to described log files you have and are required
condition in correlation. They will be refered as "parser_dir/parser_name" in
configuration files : 
<pre>
  ~/parsers/cisco/asa.parser     => cisco/asa
  ~/parsers/cisco/router.parser  => cisco/router 
  ~/parsers/squid/squid.parser   => squid/squid
</pre>

For details, see examples provided with linux/iptables and bluecoat/http but
notice that all items within a parser are assembled, in order they appears, to
form one big regex describing your log line. Each field will be captured using
regex parenthesis and are named using 'label'. Those labels will be used in
correlation to refer to those fields (see below).

Note: in the futur and if a community emerge from this code, we will provide
parsers for users who are not confident with regex writing.

##### 4. You've got log files, you've got parsers to describe them, now load it into Ratel.
Edit the ~/sources/sources.xml file to describe all log files you have.
Each log type must be defined within a <source> node.  A source node can have
one or more path (if you have multiple equipements of the say kind for example).
A source node can have one or more parsers (if multiple log lines exists into
the same file).

Please see the provided sources.xml for details and macros usage.

##### 5. Ratel can now read and parse your log files, now correlate !
Correlation rules are defined in one or more xml files stored into the ~/rules 
directory. A rule, has few mandatory fields :
* a type and a name describing the rule (see provided xml file)
* a status defining if the rule is active or not
* a flag indicating if the events that trigger that rule should be send to other
  rules in case of match. Rules are evaluated like firewall rules (one after 
  one, from the top to the bottom).
* a description which might be usefull to understand the rule :)
* a list of required parsers. The rule will be applied only on log lines that
  match the selected parsers.
* a condition : this is a boolean expression using functions (see below). If the
  condition is evaluated as True, the action is executed
* an action : this is the performed action in case of the condition is evaluated
  as True.


####### Writing a condition 
Ok, so, parsers with the "correlate" action will transform
log lines into python objects and send them to the correlation engine.  In the
correlation engine, they are no more log lines, they are "events", and you can
refer to those events using the special keyword "evt". Attributs of those events
are labels you defined previously into the parsers.

So, let's say you have a parser, for web based logs like apache, with labels
like "domain", "status", "user_agent", etc. You can refer to those
attributs/labels this way : evt.domain, evt.status, evt.user_agent, etc.

This means, in a correlation rule, if you want, let's say `"Mozilla/4.x"`
user_agent where `'x'` is any number, you can use the following expression :
`match(evt.user_agent, "Mozilla/4.\d+")`(<= this is a function, we will discuss
this right after).  
You want to match HTTP status code below 400 (sucessfullrequest) : 
`lt(evt.status, 400)`. 
There is simple arithmetic functions : lt (lowerthan), gt (greater then), 
eq (equal), le (lower than or equal), ge (greather than or equal).

Ok, you want to have Mozilla browsers who have a 2xx http status code but you
don't care of google.com and wikipedia.org domains, simply write the correlation
rule :

<pre>
(gt(evt.status, 199) AND lt(evt.status, 300)) AND match(evt.user_agent,
"Mozilla") AND NOT match(evt.domain, "google.com|wikipedia.org")
</pre>

####### Functions
A function is used into correlation rule. Each function must return
True or False and you can define your own functions (in python) ;) I should
write something about functions definitions... but have a look into
`~/ratel/functions/` directory.

##### 6. Launch it !

Simply launch Ratel with the following command line : 
```bash
$ cd /home/ratel
$ ./ratel -c /home/ratel
```
And look into the logs files (~/logs/ratel-YYYY.MM.DD.log) what's happening!

##### 7. Send me you feedback

Send me your feedback/advice/comment/logs/whatever you want!


### Events, few words...

You _SHOULD_ order events as they appears in your logs for better performances
(most common event first).

Event's name: Any name you want, it's not used except for logging purpose.

Event's action:
* drop     : discard the event
* correlate: send the event to the correlation engine
* store    : send it in database as an object (NoSQL) -- not implemented yet

To correlate _and_ store the event, use the pipe notation as follow:
"correlate|store".


