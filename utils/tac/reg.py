"""
This module contains classes of 'temporary variables', or 'virtual registers'.
These 'variables'/'registers' serve as operands of TAC instructions/native assembly instructions.
"""

from typing import Optional


# Temporary variables.
class Temp:
    def __init__(self, index: int) -> None:
        self.index = index

    def __str__(self) -> str:
        return "_T" + str(self.index)


# registers derived from temporary variables
class Reg(Temp):
    def __init__(self, id: int, name: str) -> None:
        # need to consider
        super().__init__(-id - 1)
        self.id = id
        self.name = name

        self.occupied = False
        self.used = False
        self.temp: Optional[Temp] = None

    def isUsed(self):
        return self.used

    def __str__(self) -> str:
        return self.name
