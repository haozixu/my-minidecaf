from ..program import NativeFunc, NativeProg

from abc import ABC, abstractmethod


class NativeFuncTransformPass(ABC):
    @abstractmethod
    def __call__(self, fn: NativeFunc) -> NativeFunc:
        ...


class NativeProgTransformPass(ABC):
    @abstractmethod
    def __call__(self, p: NativeProg) -> NativeProg:
        ...


class Func2ProgPassConverter(NativeProgTransformPass):
    def __init__(self, fn_transform):
        self.fn_transform = fn_transform

    def __call__(self, prog: NativeProg):
        for i, fn in enumerate(prog.funcs):
            prog.funcs[i] = self.fn_transform(fn)
        return prog
