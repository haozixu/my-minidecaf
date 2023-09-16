from utils.tac.instructions import Terminator

from ..program import BasicBlock
from ..instructions import NativeTerminator, Jump, RegBranch


class ControlFlowGraph:
    def __init__(self, nodes: list[BasicBlock]):
        self.nodes = nodes
        self.edges = [([], []) for _ in nodes]
        self.build()

    def add_edge(self, u: int, v: int):
        self.edges[u][0].append(v)
        self.edges[v][1].append(u)

    def build(self):
        label2idx = {}
        for i, bb in enumerate(self.nodes):
            label = bb.label

            # we require unique labels here
            assert label not in label2idx
            label2idx[label] = i

        for i, bb in enumerate(self.nodes):
            term = bb.terminator()
            if term is None:
                continue
            assert isinstance(term, NativeTerminator) or isinstance(term, Terminator)

            # NOTE: only NativeTerminators are considered here.
            # add Terminators check if necessary.
            match term:
                case Jump(target=tgt):
                    j = label2idx[tgt.label]
                    self.add_edge(i, j)
                case RegBranch(false_target=f_tgt, true_target=t_tgt):
                    j = label2idx[f_tgt.label]
                    k = label2idx[t_tgt.label]
                    self.add_edge(i, j)
                    self.add_edge(i, k)
                case _:
                    pass  # TODO: handle other terminators

    def __iter__(self):
        return iter(self.nodes)

    def __len__(self) -> int:
        return len(self.nodes)

    def __getitem__(self, i: int) -> BasicBlock:
        return self.nodes[i]

    def succ(self, i: int) -> list[int]:
        return self.edges[i][0]

    def pred(self, i: int) -> list[int]:
        return self.edges[i][1]
