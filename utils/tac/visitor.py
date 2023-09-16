from __future__ import annotations

from .instructions import *


class TACVisitor:
    def visit_other(self, _instr: TACInstr) -> None:
        pass

    def visit_assign(self, instr: Assign) -> None:
        self.visit_other(instr)

    def visit_load_imm32(self, instr: LoadImm32) -> None:
        self.visit_other(instr)

    def visit_unary(self, instr: Unary) -> None:
        self.visit_other(instr)

    def visit_binary(self, instr: Binary) -> None:
        self.visit_other(instr)

    def visit_jump(self, instr: Jump) -> None:
        self.visit_other(instr)

    def visit_branch(self, instr: Branch) -> None:
        self.visit_other(instr)

    def visit_return(self, instr: Return) -> None:
        self.visit_other(instr)

    def visit_call(self, instr: Call) -> None:
        self.visit_other(instr)

    def visit_comment(self, instr: Comment) -> None:
        self.visit_other(instr)
