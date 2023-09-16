from utils.tac.program import TACBlock, TACFunc, TACProg

from dataclasses import dataclass
from typing import Iterable

# export alias
BasicBlock = TACBlock
NativeFunc = TACFunc
NativeProg = TACProg


@dataclass
class StackObject:
    offset: int | None
    size: int


# Returns the total size of StackObjects
def assign_stack_offsets(objs: Iterable[StackObject]) -> int:
    offset = 0
    for obj in objs:
        obj.base = offset
        offset += obj.size
    return offset


def new_instr_buffer():
    buf = []
    emit = lambda i: buf.append(i)
    return buf, emit
