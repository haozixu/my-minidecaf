from .manage import NativeFuncTransformPass

from ..program import BasicBlock, NativeFunc, new_instr_buffer
from ..instructions import *
from ..reg import *

from ..analysis.control_flow_graph import ControlFlowGraph
from ..analysis.liveness import LivenessAnalyzer, BlockLiveness

import random
from collections import deque


class LocalRegAllocator(NativeFuncTransformPass):
    def __init__(self):
        # stack objects with a linear order
        self.stack_objects: deque[StackObject] = deque()
        # stack slots mapping: vreg => stack object
        self.stack_slots: dict[Reg, StackObject] = {}

    def get_stack_slot(self, vreg: Reg) -> StackObject:
        if vreg not in self.stack_slots:
            # the position (offset) for this stack object is not determined yet
            stack_obj = StackObject(None, WORD_SIZE)
            self.stack_objects.append(stack_obj)
            self.stack_slots[vreg] = stack_obj
        return self.stack_slots[vreg]

    # Allocate physical registers for each function (subroutine)
    def __call__(self, fn: NativeFunc) -> NativeFunc:
        self.stack_objects = deque()
        self.stack_slots = {}
        self.fn = fn

        cfg = ControlFlowGraph(fn.blocks)
        anaylzer = LivenessAnalyzer()

        while True:
            bbls = anaylzer(cfg, do_instr_level=True)

            # TODO: consider stack objects of function parameters
            for i, bb in enumerate(cfg):
                self.do_local_alloc(bb, bbls[i], i == 0)

            done = all(self.check_and_expand_stack_ops(bb) for bb in cfg)
            if done:
                break

        # replace virtual registers
        for bb in cfg:
            for instr in bb:
                for vreg, preg in instr.reg_map:
                    instr.replace_operand(vreg, preg)

        # attach stack objects information
        fn.stack_objects = self.stack_objects
        return fn

    def do_local_alloc(self, bb: BasicBlock, bl: BlockLiveness, is_entry: bool):
        # currently allocated physical register <=> virtual register bindings
        phys2virt: dict[Reg, Reg] = {}
        virt2phys: dict[Reg, Reg] = {}

        def unbind(p: Reg):
            virt2phys.pop(phys2virt.pop(p))

        def bind(v: Reg, p: Reg):
            phys2virt[p] = v
            virt2phys[v] = p

        def filter_vregs(regs: list[Reg]) -> list[Reg]:
            return [r for r in regs if is_virt_reg(r)]

        buf, emit = new_instr_buffer()
        for instr in bb:
            instr.reg_map: list[tuple[Reg, Reg]] = []

            # 2 phases here: allocate for source operands and then destination operands
            vregs = (filter_vregs(instr.uses()), filter_vregs(instr.defs()))
            need_load = (True, False)

            for stage in range(2):
                pregs = []
                for v in vregs[stage]:
                    if v in virt2phys:
                        # virtual register v already have a corresponding physical register
                        pregs.append(virt2phys[v])
                        continue

                    # TODO: preferred regs first?
                    free_reg_found = False
                    for p in GPRegs.ALLOCATABLE:
                        if p in phys2virt and phys2virt[p] not in instr.live_out:
                            unbind(p)
                        if p not in phys2virt:
                            # physical register p is available
                            free_reg_found = True
                            break
                    if not free_reg_found:
                        # no free physical register left. find a victim and evict it.
                        candidates = tuple(set(GPRegs.ALLOCATABLE) - set(pregs))
                        p = random.choice(candidates)
                        victim = phys2virt[p]
                        emit(StackStore(p, self.get_stack_slot(victim)))
                        unbind(p)

                    bind(v, p)
                    pregs.append(p)
                    if need_load[stage]:
                        emit(StackLoad(p, self.get_stack_slot(v)))

                # replacement is done later. just record mapping here.
                # NOTE: 1. one iteration may not be sufficient to complete register allocation
                # 2. global vreg => preg mapping is not used as SSA property is not guaranteed
                instr.reg_map += list(zip(vregs[stage], pregs))

            emit(instr)

        # We have to spill all active regs in live_out set onto stack
        for v in bl.live_out:
            if v in virt2phys:
                emit(StackStore(virt2phys[v], self.get_stack_slot(v)))

        bb.instrs = buf

    def check_and_expand_stack_ops(self, bb: BasicBlock) -> bool:
        ok = True
        buf, emit = new_instr_buffer()
        # NOTE: all stack stores are conservatively transformed into LoadStackAddr + Store

        for instr in bb:
            match instr:
                case StackStore(src=src, base=base, offset=offset):
                    ok = False
                    addr = self.fn.new_temp()
                    emit(LoadStackAddr(addr, base, offset))
                    emit(Store(src, addr))

                case SPAdd(delta=delta, src=src) if not is_imm12(delta) and src is None:
                    ok = False
                    tmp = self.fn.new_temp()
                    emit(LoadImm32(tmp, delta))
                    emit(SPAdd(delta, tmp))

                case _:
                    emit(instr)

        bb.instrs = buf
        return ok
