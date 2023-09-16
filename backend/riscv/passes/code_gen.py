from .manage import NativeFuncTransformPass

from ..program import NativeFunc, assign_stack_offsets, new_instr_buffer
from ..instructions import *
from ..reg import *

from utils.tac import instructions as tacinstr


class AsmCodeEmitter(NativeFuncTransformPass):
    def __init__(self):
        self.exit_bb: BasicBlock | None = None

    def __call__(self, fn: NativeFunc) -> NativeFunc:
        assert hasattr(fn, "stack_objects")

        self.emit_prologue_epilogue(fn)
        self.replace_intermediate_instrs(fn)
        return fn

    def emit_prologue_epilogue(self, fn: NativeFunc):
        is_leaf = True  # !is_leaf => save ra
        saved_regs = set()
        for bb in fn.blocks:
            for instr in bb:
                if isinstance(instr, tacinstr.Call):
                    is_leaf = False

                for reg in instr.operands():
                    if reg in GPRegs.CALLEE_SAVED:
                        saved_regs.add(reg)

        saved_regs = sorted(list(saved_regs), key=lambda r: -r.index)
        if not is_leaf:
            saved_regs = [GPRegs.RA] + saved_regs

        saved_regs_size = len(saved_regs) * WORD_SIZE
        stack_objs_size = sum(map(lambda obj: obj.size, fn.stack_objects))
        frame_size = saved_regs_size + stack_objs_size

        prologue, epilogue = [], []

        is_huge_frame = frame_size >= 2048
        aux_reg = GPRegs.T0 if is_huge_frame else None
        # saved_regs_size (<= 13 * 4) always fits in imm12
        for i, reg in enumerate(saved_regs):
            prologue.append(Store(reg, GPRegs.SP, i * WORD_SIZE - saved_regs_size))
        if is_huge_frame:
            prologue.append(LoadImm32(GPRegs.T0, -frame_size))
        if frame_size > 0:
            prologue.append(SPAdd(-frame_size, aux_reg))

        if is_huge_frame:
            epilogue.append(LoadImm32(GPRegs.T0, frame_size))
        if frame_size > 0:
            epilogue.append(SPAdd(frame_size, aux_reg))
        for i, reg in enumerate(saved_regs):
            epilogue.append(Load(reg, GPRegs.SP, i * WORD_SIZE - saved_regs_size))
        epilogue.append(NativeRet())

        # always treat the first basic block as the entry point
        entry_bb = fn.blocks[0]
        entry_bb.instrs = prologue + entry_bb.instrs

        if frame_size > 0:
            self.exit_bb = BasicBlock(fn.name + ".exit")
            self.exit_bb.instrs = epilogue
            fn.blocks.append(self.exit_bb)

    def replace_intermediate_instrs(self, fn: NativeFunc):
        """
        In this phase, we finalize stack frame to determine every stack object's
        real position, therefore these stack related intermediate instructions can
        be replaced by their native forms. Other intermediate instructions such
        as double-target branches are also transformed into their final representations.
        (e.g one conditional branch or a conditional branch followed by an jump)
        """
        assign_stack_offsets(fn.stack_objects)

        sp_offset = 0
        for i, bb in enumerate(fn.blocks):
            next_bb = fn.blocks[i + 1] if i + 1 < len(fn.blocks) else None
            buf, emit = new_instr_buffer()
            for instr in bb:
                match instr:
                    # stack related
                    case LoadStackAddr(dst=dst, base=base):
                        offset = instr.offset + base.offset - sp_offset
                        if is_imm12(offset):
                            emit(AddI(dst, GPRegs.SP, offset))
                        else:
                            emit(LoadImm32(dst, offset))
                            emit(Binary(BinaryOp.ADD, dst, GPRegs.SP, dst))

                    case StackLoad(dst=dst, base=base):
                        offset = instr.offset + base.offset - sp_offset
                        if is_imm12(offset):
                            emit(Load(dst, GPRegs.SP, offset))
                        else:
                            emit(LoadImm32(dst, offset))
                            emit(Binary(BinaryOp.ADD, dst, GPRegs.SP, dst))
                            emit(Load(dst, dst))

                    case StackStore(src=src, base=base):
                        offset = instr.offset + base.offset - sp_offset
                        assert is_imm12(offset)
                        emit(Store(src, GPRegs.SP, offset))

                    case SPAdd(delta=delta):
                        sp_offset += delta

                    # control flow related
                    case Jump(target=target):
                        if next_bb is not target:
                            emit(instr)

                    case RegBranch(cond=cond, false_target=f_tgt, true_target=t_tgt):
                        if next_bb is f_tgt:
                            emit(CmpBranch(CmpBranchOp.BNE, t_tgt, cond, GPRegs.ZERO))
                        elif next_bb is t_tgt:
                            emit(CmpBranch(CmpBranchOp.BEQ, f_tgt, cond, GPRegs.ZERO))
                        else:
                            emit(CmpBranch(CmpBranchOp.BNE, t_tgt, cond, GPRegs.ZERO))
                            emit(Jump(f_tgt))

                    case tacinstr.Return(value=val):
                        if val is not None:
                            emit(Move(GPRegs.A0, val))
                        if self.exit_bb is None:
                            emit(NativeRet())
                        else:
                            if next_bb is not self.exit_bb:
                                emit(Jump(self.exit_bb))

                    case _:
                        emit(instr)

            bb.instrs = buf
