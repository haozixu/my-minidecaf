import argparse
import sys

from backend.riscv.entry import backend_passes, ProgramTranslator
from backend.riscv.misc import AsmCodePrinter

from frontend.ast.tree import Program
from frontend.lexer import lexer
from frontend.parser import parser
from frontend.passes.tacgen import TACGen
from frontend.passes.namer import Namer
from frontend.passes.typer import Typer
from utils.printtree import TreePrinter
from utils.tac.program import TACProg


def parse_args():
    parser = argparse.ArgumentParser(description="MiniDecaf compiler")
    parser.add_argument("--input", type=str, help="the input C file")
    parser.add_argument("--parse", action="store_true", help="output parsed AST")
    parser.add_argument("--tac", action="store_true", help="output transformed TAC")
    parser.add_argument("--riscv", action="store_true", help="output generated RISC-V")
    return parser.parse_args()


def read_code(fileName):
    with open(fileName, "r") as f:
        return f.read()


# The parser stage: MiniDecaf code -> Abstract syntax tree
def step_parse(args: argparse.Namespace):
    code = read_code(args.input)
    r: Program = parser.parse(code, lexer=lexer)

    errors = parser.error_stack
    if errors:
        print("\n".join(map(str, errors)), file=sys.stderr)
        exit(1)

    return r


# IR generation stage: Abstract syntax tree -> Three-address code
def step_tac(p: Program):
    namer = Namer()
    p = namer.transform(p)
    typer = Typer()
    p = typer.transform(p)

    tacgen = TACGen()
    tac_prog = tacgen.transform(p)

    return tac_prog


# Target code generation stage: Three-address code -> RISC-V assembly code
def step_asm(p: TACProg):
    translator = ProgramTranslator()
    prog = translator(p)

    for transform in backend_passes:
        prog = transform(prog)
    return prog


# hope all of you happiness
# enjoy potato chips


def main():
    args = parse_args()

    def _parse():
        r = step_parse(args)
        # print("\nParsed AST:\n")
        # printer = TreePrinter(indentLen=2)
        # printer.print(r)
        return r

    def _tac():
        tac = step_tac(_parse())
        # print("\nGenerated TAC:\n")
        # tac.printTo()
        return tac

    def _asm():
        asm = step_asm(_tac())
        # print("\nGenerated ASM:\n")
        # print(asm)
        return asm

    if args.riscv:
        prog = _asm()
        printer = AsmCodePrinter()
        printer.print(prog)
    elif args.tac:
        prog = _tac()
        prog.print()
    elif args.parse:
        prog = _parse()
        printer = TreePrinter(indent_len=2)
        printer.print(prog)
    else:
        print("No action.")


if __name__ == "__main__":
    main()
