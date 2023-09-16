from utils.tac.instructions import TACInstr, UnaryOp, BinaryOp

from .reg import *
from .program import BasicBlock, StackObject

from enum import Enum, auto, unique


def _format2(d: Reg, s: Reg) -> str:
    return "%s, %s" % (reg_name(d), reg_name(s))


def _format3(d: Reg, s1: Reg, s2: Reg) -> str:
    return "%s, %s, %s" % (reg_name(d), reg_name(s1), reg_name(s2))


def _format_ldst(r: Reg, base: Reg, offset: int) -> str:
    return "%s, %d(%s)" % (reg_name(r), offset, reg_name(base))


def is_imm12(imm: int) -> bool:
    return -2048 <= imm < 2048


@unique
class CmpBranchOp(Enum):
    BEQ = auto()
    BNE = auto()
    BLT = auto()
    BGE = auto()
    # BLTU = auto()
    # BGEU = auto()


# Native instructions.
class NativeInstr(TACInstr):
    ...


class NativeTerminator(NativeInstr):
    ...


class LoadImm32(NativeInstr):
    def __init__(self, dst: Reg, value: int):
        super().__init__([dst], [])
        self.dst = dst
        self.value = value

    def __str__(self) -> str:
        return "li %s, %d" % (reg_name(self.dst), self.value)


class Move(NativeInstr):
    def __init__(self, dst: Reg, src: Reg):
        super().__init__([dst], [src])
        self.dst = dst
        self.src = src

    def __str__(self) -> str:
        return "mv " + _format2(self.dst, self.src)


class Unary(NativeInstr):
    def __init__(self, op: UnaryOp, dst: Reg, src: Reg):
        super().__init__([dst], [src])
        self.op = str(op)[8:].lower()
        self.dst = dst
        self.src = src

    def __str__(self) -> str:
        return self.op + " " + _format2(self.dst, self.src)


class Binary(NativeInstr):
    def __init__(self, op: BinaryOp, dst: Reg, src1: Reg, src2: Reg):
        super().__init__([dst], [src1, src2])
        self.op = str(op)[9:].lower()
        self.dst = dst
        self.src1 = src1
        self.src2 = src2

    def __str__(self) -> str:
        return self.op + " " + _format3(self.dst, self.src1, self.src2)


class AddI(NativeInstr):
    def __init__(self, dst: Reg, src: Reg, imm: int):
        super().__init__([dst], [src])
        self.dst = dst
        self.src = src
        self.imm = imm

    def __str__(self) -> str:
        assert is_imm12(self.imm)
        return "addi %s, %s, %d" % (reg_name(self.dst), reg_name(self.src), self.imm)


# Intermediate branch instruction. This should not appear in final code.
# e.g. br a0, .L1, .L2
# =>   beq a0, zero, .L1
#      j .L2
class RegBranch(NativeTerminator):
    def __init__(self, cond: Reg, false_target: BasicBlock, true_target: BasicBlock):
        super().__init__([], [cond])
        self.cond = cond
        self.false_target = false_target
        self.true_target = true_target

    def __str__(self) -> str:
        return "br %s, %s, %s" % (
            reg_name(self.cond, self.false_target.label, self.true_target.label)
        )


class CmpBranch(NativeTerminator):
    def __init__(self, op: CmpBranchOp, target: BasicBlock, src1: Reg, src2: Reg):
        super().__init__([], [src1, src2])
        self.op = str(op)[11:].lower()
        self.src1 = src1
        self.src2 = src2
        self.target = target

    def __str__(self) -> str:
        return "%s %s, %s, %s" % (
            self.op,
            reg_name(self.src1),
            reg_name(self.src2),
            self.target.label,
        )


class Jump(NativeTerminator):
    def __init__(self, target: BasicBlock):
        super().__init__([], [])
        self.target = target

    def __str__(self) -> str:
        return "j %s" % self.target.label


class NativeRet(NativeTerminator):
    def __init__(self):
        super().__init__([], [])

    def __str__(self) -> str:
        return "ret"


class Load(NativeInstr):
    def __init__(self, dst: Reg, base: Reg, offset: int = 0):
        super().__init__([dst], [base])
        self.dst = dst
        self.base = base
        self.offset = offset

    def __str__(self) -> str:
        return "lw " + _format_ldst(self.dst, self.base, self.offset)


class Store(NativeInstr):
    def __init__(self, src: Reg, base: Reg, offset: int = 0):
        super().__init__([], [src, base])
        self.src = src
        self.base = base
        self.offset = offset

    def __str__(self) -> str:
        return "sw " + _format_ldst(self.src, self.base, self.offset)


class LoadStackAddr(NativeInstr):
    def __init__(self, dst: Reg, base: StackObject, offset: int = 0):
        super().__init__([dst], [])
        self.dst = dst
        self.base = base
        self.offset = offset

    def __str__(self) -> str:
        return "load-addr %s, stack-obj[%s]+%d" % (
            reg_name(self.dst),
            hex(id(self.base)),
            self.offset,
        )


class StackLoad(NativeInstr):
    def __init__(self, dst: Reg, base: StackObject, offset: int = 0):
        super().__init__([dst], [])
        self.dst = dst
        self.base = base
        self.offset = offset

    def __str__(self) -> str:
        return "lw %s, stack-obj[%s]+%d" % (
            reg_name(self.dst),
            hex(id(self.base)),
            self.offset,
        )


class StackStore(NativeInstr):
    def __init__(self, src: Reg, base: StackObject, offset: int = 0):
        super().__init__([], [src])
        self.src = src
        self.base = base
        self.offset = offset

    def __str__(self) -> str:
        return "sw %s, stack-obj[%s]+%d" % (
            reg_name(self.src),
            hex(id(self.base)),
            self.offset,
        )


# NOTE: sp is not in defs/uses list
class SPAdd(NativeInstr):
    def __init__(self, delta: int, src: Reg | None = None):
        if src is None:
            super().__init__([], [])
        else:
            super().__init__([], [src])
        self.delta = delta
        self.src = src

    def __str__(self) -> str:
        s = "sp-add %d" % (self.delta)
        if isinstance(self.src, Reg):
            s += " (%s)" % reg_name(self.src)
        return s
