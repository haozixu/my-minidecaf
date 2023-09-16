from ..program import BasicBlock, NativeFunc, NativeProg
from ..instructions import *
from ..reg import *

from utils.tac import instructions as tacinstr
from utils.tac.program import TACFunc, TACProg
from utils.tac.visitor import TACVisitor


class FunctionTranslator(TACVisitor):
    def __call__(self, tac_fn: TACFunc) -> NativeFunc:
        self.bb_map: dict[str, BasicBlock] = {}  # bb_label -> new bb
        for src_bb in tac_fn.blocks:
            label = src_bb.label
            self.bb_map[label] = BasicBlock(label)

        bbs = []
        for src_bb in tac_fn.blocks:
            self.cur_bb = self.bb_map[src_bb.label]
            for instr in src_bb:
                instr.accept(self)
            bbs.append(self.cur_bb)

        native_fn = NativeFunc(
            tac_fn.name,
            tac_fn.num_params,
            bbs,
        )
        return native_fn

    # default behavior: copy instruction (reference)
    def visit_other(self, instr: tacinstr.TACInstr) -> None:
        self.cur_bb.add(instr)

    def visit_return(self, ret: tacinstr.Return) -> None:
        self.cur_bb.add(ret)

    def visit_jump(self, jump: tacinstr.Jump) -> None:
        target = self.bb_map[jump.target.label]
        self.cur_bb.add(Jump(target))

    def visit_branch(self, br: tacinstr.Branch) -> None:
        false_target = self.bb_map[br.false_target.label]
        true_target = self.bb_map[br.true_target.label]
        self.cur_bb.add(RegBranch(br.cond, false_target, true_target))

    def visit_load_imm32(self, li32: tacinstr.LoadImm32) -> None:
        self.cur_bb.add(LoadImm32(li32.dst, li32.value))

    def visit_unary(self, unary: tacinstr.Unary) -> None:
        self.cur_bb.add(Unary(unary.op, unary.dst, unary.operand))

    def visit_binary(self, binary: tacinstr.Binary) -> None:
        """
        Some TAC instructions cannot be simply turned into their corresponding
        machine (native) instructions (no direct one-to-one mapping).
        Here are some options:
        1. Keep their intermediate TAC forms and handle them later during 
        the final code emission phase.
        2. Break them down into fine-grained instructions. If extra Temps
        (virtual registers) are needed, it's better to follow this approach.
        """
        self.cur_bb.add(Binary(binary.op, binary.dst, binary.lhs, binary.rhs))


# Translates a TAC program into a native program
class ProgramTranslator:
    def __call__(self, prog: TACProg) -> NativeProg:
        trans = FunctionTranslator()
        dst_fns = [trans(src_fn) for src_fn in prog.funcs]
        return NativeProg(dst_fns)
