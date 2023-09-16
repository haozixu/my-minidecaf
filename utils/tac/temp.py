"""
This module contains classes of 'temporary variables', or 'virtual registers'.
These 'variables'/'registers' serve as operands of TAC instructions/native assembly instructions.
"""


# Temporary variables.
class Temp:
    def __init__(self, index: int) -> None:
        self.index = index

    def __repr__(self) -> str:
        return "%%%d" % self.index

    def __str__(self) -> str:
        return "_T%d" % self.index

    def __hash__(self) -> int:
        return hash(self.index)

    def __eq__(self, other) -> bool:
        if not isinstance(other, Temp):
            return False
        return self.index == other.index
