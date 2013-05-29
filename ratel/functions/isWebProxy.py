#!/usr/bin/env python
import re
from base64 import b64encode

# This functions return True if the specified argument contains
# well known web proxy signatures
#
# Example:
# isWebProxy(evt.url)

_signature = "isWebProxy\(([^)]+)\)"


def main(attribut):
    patterns = [
        b64encode('www.')[:-2],
        b64encode('http://')[:-2],
        "http:=2f=2f",
        "\\?=&=",
        "ajax=true"
    ]

    try:
        for p in patterns:
            if re.search(p, attribut):
                return True
    except re.error:
        pass
    return False


if __name__ == "__main__":
    # This code is only for testing the main function.
    # python file_name.py
    print main("www.google.com") # False
    print main("index.php?=&=www.abc.com") # True

