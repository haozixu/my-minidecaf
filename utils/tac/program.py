"""
This module contains constructs of a TAC program.

A TAC program consists of several TAC functions and directives.

TAC Functions can be further break down into Blocks. Blocks are containers of TAC instructions.
TAC Functions will be translated into assembly sub-routines.

'Directives' here are also called 'pseudo instructions', which provide extra information of the program,
such as external variable declaration.
"""

from .instructions import TACInstr
from .temp import Temp


# A TAC basic block
class TACBlock:
    def __init__(self, label: str) -> None:
        self.label = label
        self.instrs: list[TACInstr] = []

    def __iter__(self):
        return iter(self.instrs)

    def __len__(self) -> int:
        return len(self.instrs)

    def __getitem__(self, i: int) -> TACInstr:
        return self.instrs[i]

    def empty(self) -> bool:
        return len(self.instrs) == 0

    def add(self, instr: TACInstr) -> None:
        self.instrs.append(instr)

    def last_instr(self) -> TACInstr:
        return self.instrs[-1]

    def terminator(self) -> TACInstr | None:
        return self.instrs[-1] if not self.empty() else None

    def __repr__(self) -> str:
        return "Block<%s>" % self.label

    def __str__(self) -> str:
        s = self.label + ":"
        for instr in self.instrs:
            s += "\n    " + str(instr)
        return s


class TACFunc:
    def __init__(
        self, name: str, num_params: int = 0, blocks: list[TACBlock] | None = None
    ) -> None:
        self.name = name
        self.num_params = num_params
        self.temp_used = num_params
        self.blocks = blocks if blocks is not None else []

    def add_block(self, block: TACBlock) -> None:
        self.blocks.append(block)

    def new_temp(self) -> Temp:
        self.temp_used += 1
        return Temp(self.temp_used)

    def __repr__(self) -> str:
        return "Func<%s>" % self.name

    def __str__(self) -> str:
        s = self.name + ":"
        for block in self.blocks:
            s += "\n" + str(block)
        return s


# A TAC program consists of several TAC functions.
# TODO: global vars
class TACProg:
    def __init__(self, funcs: list[TACFunc]) -> None:
        self.funcs = funcs
    
    def __str__(self) -> str:
        return "\n".join(str(fn) for fn in self.funcs)

    def print(self) -> None:
        for func in self.funcs:
            print(str(func))
