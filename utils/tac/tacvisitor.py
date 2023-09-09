from __future__ import annotations

from .tacinstr import *


class TACVisitor:
   def visit_other(self, instr: TACInstr) -> None:
        pass

   def visit_assign(self, instr: Assign) -> None:
        self.visit_other(instr)

   def visit_load_imm4(self, instr: LoadImm4) -> None:
        self.visit_other(instr)

   def visit_unary(self, instr: Unary) -> None:
        self.visit_other(instr)

   def visit_binary(self, instr: Binary) -> None:
        self.visit_other(instr)

   def visit_branch(self, instr: Branch) -> None:
        self.visit_other(instr)

   def visit_cond_branch(self, instr: CondBranch) -> None:
        self.visit_other(instr)

   def visit_return(self, instr: Return) -> None:
        self.visit_other(instr)

   def visit_memo(self, instr: Memo) -> None:
        self.visit_other(instr)

   def visit_mark(self, instr: Mark) -> None:
        self.visit_other(instr)
