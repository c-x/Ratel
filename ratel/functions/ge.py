#!/usr/bin/python

"""
Return True if 'left' is greather than or equal to 'right'
"""

_signature = "ge\(([^,]+),([^)]+)\)"


def main(left, right):
    a = 0
    b = 0
    try:
        a = int(left)
        b = int(right)
    except TypeError:
        pass

    return a >= b


if __name__ == "__main__":
    print main("654", 400)
    print main(400, "654")
    print main("401", "4'00")
    print main("654", 0x400)
