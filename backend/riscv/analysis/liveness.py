from dataclasses import dataclass

from .control_flow_graph import ControlFlowGraph
from ..reg import Reg


@dataclass
class BlockLiveness:
    define: set[Reg]
    live_use: set[Reg]
    live_in: set[Reg]
    live_out: set[Reg]


@dataclass
class BlockInstructionLiveness:
    live_in_seqs: list[set[Reg]]
    live_out_seqs: list[set[Reg]]


# NOTE: implementation choices
# 1. use separate data classes to store liveness information
# 2. attach liveness results to existing objects
class LivenessAnalyzer:
    def __call__(
        self,
        graph: ControlFlowGraph,
        do_instr_level: bool = False,
        attach_props: bool = False,
    ) -> list[BlockLiveness]:
        res: list[BlockLiveness] = []
        # Compute define and live_use first. They will not change during the iterations.
        for bb in graph:
            define: set[Reg] = set()
            live_use: set[Reg] = set()
            for instr in bb:
                # live_use = live_use ∪ (use - def)
                for u in instr.uses():
                    if u not in define:
                        live_use.add(u)
                define.update(instr.defs())

            # live_in is initialized to live_use
            res.append(BlockLiveness(define, live_use, live_use.copy(), set()))

        # Iteratively update live_in and live_out
        changed = True
        while changed:
            changed = False
            for i in range(len(graph)):
                bl = res[i]
                for j in graph.succ(i):
                    bl.live_out.update(res[j].live_in)

                # live_in = live_use ∪ (live_out - def)
                before = len(bl.live_in)
                bl.live_in.update(bl.live_out - bl.define)
                after = len(bl.live_in)

                if before != after:
                    changed = True

        if attach_props:
            for i, bb in enumerate(graph):
                bl = res[i]
                props = (prop for prop in dir(bl) if not prop.startswith("__"))
                for prop in props:
                    setattr(bb, prop, getattr(bl, prop))

        if not do_instr_level:
            return res

        # Compute live_in & live_out for each instruction
        for i, bb in enumerate(graph):
            live = res[i].live_out.copy()
            for instr in reversed(bb):
                instr.live_out = live.copy()
                live.difference_update(instr.defs())
                live.update(instr.uses())
                instr.live_in = live.copy()
        return res
