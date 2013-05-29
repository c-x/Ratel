#!/usr/bin/env python
import re

# Match a regular expression or a word.
# This function is case sensitive.
#
#
# Example:
# match(evt.url, "domaind\.tld")
# match(evt.ip_src, "127\.\d+\.\d+\.\d+")

_signature = "match\(([^,]+),([^)]+)\)"


def main(attribut, pattern):
    try:
        reg_t = re.compile(pattern)
        if reg_t.search(attribut):
            ret = True
    except re.error:
        ret = False
    return ret


if __name__ == "__main__":
    # This code is only for testing the main function.
    # python file_name.py
    print main("www.google.com", "o.l") # True
    print main("Hello   world !", "lo\\s+w") # True

