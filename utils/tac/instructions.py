"""
Instructions of TAC Programs.
"""

from enum import Enum, auto, unique
from typing import TYPE_CHECKING

from .visitor import TACVisitor
from .temp import Temp

if TYPE_CHECKING:
    from .program import TACBlock


# Kinds of unary operations.
@unique
class UnaryOp(Enum):
    NEG = auto()
    NOT = auto()
    SEQZ = auto()


# Kinds of binary operations.
@unique
class BinaryOp(Enum):
    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()
    REM = auto()
    EQU = auto()
    NEQ = auto()
    SLT = auto()
    LEQ = auto()
    SGT = auto()
    GEQ = auto()
    AND = auto()
    OR = auto()


class TACInstr:
    def __init__(self, dsts: list[Temp], srcs: list[Temp]) -> None:
        self.dsts = dsts
        self.srcs = srcs

    def defs(self) -> list[Temp]:
        return self.dsts

    def uses(self) -> list[Temp]:
        return self.srcs

    def temps(self) -> list[Temp]:
        return self.defs() + self.uses()

    def operands(self) -> list[Temp]:
        return self.temps()

    def accept(self, v: TACVisitor) -> None:
        v.visit_other(self)

    def replace_operand(self, old: Temp, new: Temp):
        # 1. common `regs`
        self.srcs = [new if r == old else r for r in self.srcs]
        self.dsts = [new if r == old else r for r in self.dsts]
        # 2. other properties
        for prop in dir(self):
            if prop.startswith("__"):
                continue
            val = getattr(self, prop)
            if isinstance(val, Temp) and val == old:
                setattr(self, prop, new)


# Base class for basic block terminating instructions.
class Terminator(TACInstr):
    pass


# Assignment instruction.
class Assign(TACInstr):
    def __init__(self, dst: Temp, src: Temp) -> None:
        super().__init__([dst], [src])
        self.dst = dst
        self.src = src

    def __str__(self) -> str:
        return "%s = %s" % (self.dst, self.src)

    def accept(self, v: TACVisitor) -> None:
        v.visit_assign(self)


# Loading an immediate 32-bit constant.
class LoadImm32(TACInstr):
    def __init__(self, dst: Temp, value: int) -> None:
        super().__init__([dst], [])
        self.dst = dst
        self.value = value

    def __str__(self) -> str:
        return "%s = %d" % (self.dst, self.value)

    def accept(self, v: TACVisitor) -> None:
        v.visit_load_imm32(self)


# Unary operations.
class Unary(TACInstr):
    def __init__(self, op: UnaryOp, dst: Temp, operand: Temp) -> None:
        super().__init__([dst], [operand])
        self.op = op
        self.dst = dst
        self.operand = operand

    def __str__(self) -> str:
        op_map = {UnaryOp.NEG: "neg", UnaryOp.NOT: "bitnot", UnaryOp.SEQZ: "iszero"}
        return "%s = %s %s" % (
            self.dst,
            op_map[self.op],
            self.operand,
        )

    def accept(self, v: TACVisitor) -> None:
        v.visit_unary(self)


# Binary Operations.
class Binary(TACInstr):
    def __init__(self, op: BinaryOp, dst: Temp, lhs: Temp, rhs: Temp) -> None:
        super().__init__([dst], [lhs, rhs])
        self.op = op
        self.dst = dst
        self.lhs = lhs
        self.rhs = rhs

    def __str__(self) -> str:
        op_str = {
            BinaryOp.ADD: "+",
            BinaryOp.SUB: "-",
            BinaryOp.MUL: "*",
            BinaryOp.DIV: "/",
            BinaryOp.REM: "%",
            BinaryOp.EQU: "==",
            BinaryOp.NEQ: "!=",
            BinaryOp.SLT: "<",
            BinaryOp.LEQ: "<=",
            BinaryOp.SGT: ">",
            BinaryOp.GEQ: ">=",
            BinaryOp.AND: "&&",
            BinaryOp.OR: "||",
        }[self.op]
        return "%s = (%s %s %s)" % (self.dst, self.lhs, op_str, self.rhs)

    def accept(self, v: TACVisitor) -> None:
        v.visit_binary(self)


# Jump (branch without condition) instruction.
class Jump(Terminator):
    def __init__(self, target: "TACBlock") -> None:
        super().__init__([], [])
        self.target = target

    def __str__(self) -> str:
        return "jump %s" % str(self.target.label)

    def accept(self, v: TACVisitor) -> None:
        v.visit_jump(self)


# Branching with conditions.
class Branch(Terminator):
    def __init__(
        self, cond: Temp, false_target: "TACBlock", true_target: "TACBlock"
    ) -> None:
        super().__init__([], [cond])
        self.cond = cond
        self.false_target = false_target
        self.true_target = true_target

    def __str__(self) -> str:
        return "br %s, %s, %s" % (
            self.cond,
            self.false_target.label,
            self.true_target.label,
        )

    def accept(self, v: TACVisitor) -> None:
        v.visit_branch(self)


# Return instruction.
class Return(Terminator):
    def __init__(self, value: Temp | None) -> None:
        if value is None:
            super().__init__([], [])
        else:
            super().__init__([], [value])
        self.value = value

    def __str__(self) -> str:
        return "return" if (self.value is None) else ("return " + str(self.value))

    def accept(self, v: TACVisitor) -> None:
        v.visit_return(self)


# Function call.
class Call(TACInstr):
    def __init__(self, callee: str, dst: Temp, args: list[Temp]):
        super().__init__([dst], args.copy())
        self.callee = callee
        self.dst = dst
        self.args = args.copy()

    def __str__(self) -> str:
        return "%s = %s(%s)" % (self.dst, self.callee, ",".join(self.args))


# Annotation (used for debugging).
class Comment(TACInstr):
    def __init__(self, msg: str) -> None:
        super().__init__([], [])
        self.msg = msg

    def __str__(self) -> str:
        return "# %s" % self.msg

    def accept(self, v: TACVisitor) -> None:
        v.visit_comment(self)
