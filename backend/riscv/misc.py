from .program import NativeProg


class AsmCodePrinter:
    def print(self, prog: NativeProg):
        print("    .text")
        print("    .global main\n")
        print(str(prog))
