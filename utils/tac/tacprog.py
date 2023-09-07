"""
This module contains constructs of a TAC program.

A TAC program consists of several TAC functions and directives.

TAC Functions can be further break down into Blocks. Blocks are containers of TAC instructions.
TAC Functions will be translated into assembly sub-routines.

'Directives' here are also called 'pseudo instructions', which provide extra information of the program,
such as external variable declaration.
"""

from utils.label.funclabel import FuncLabel

from .tacinstr import TACInstr


# TODO
class TACBlock:
    pass


# TODO: TACFunc -> multiple TACBlocks
class TACFunc:
    def __init__(self, entry: FuncLabel, numArgs: int) -> None:
        self.entry = entry
        self.numArgs = numArgs
        self.instrSeq = []
        self.tempUsed = 0

    def getInstrSeq(self) -> list[TACInstr]:
        return self.instrSeq

    def getUsedTempCount(self) -> int:
        return self.tempUsed

    def add(self, instr: TACInstr) -> None:
        self.instrSeq.append(instr)

    def printTo(self) -> None:
        for instr in self.instrSeq:
            if instr.isLabel():
                print(instr)
            else:
                print("    " + str(instr))


# A TAC program consists of several TAC functions.
class TACProg:
    def __init__(self, funcs: list[TACFunc]) -> None:
        self.funcs = funcs

    def printTo(self) -> None:
        for func in self.funcs:
            func.printTo()
