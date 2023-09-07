from utils.label.label import Label
from utils.tac.nativeinstr import NativeInstr


class AsmCodePrinter:
    INDENTS = "    "
    COMMENT_PROMPT = "#"

    def __init__(self) -> None:
        self.buffer = ""

    def printf(self, fmt: str, **args):
        self.buffer += self.INDENTS + fmt.format(**args)

    def println(self, fmt: str, **args):
        self.buffer += self.INDENTS + fmt.format(**args) + "\n"

    def print_label(self, label: Label):
        self.buffer += str(label.name) + ":\n"

    def print_instr(self, instr: NativeInstr):
        if instr.isLabel():
            self.buffer += str(instr.label) + ":"
        else:
            self.buffer += self.INDENTS + str(instr)
        self.buffer += "\n"

    def print_comment(self, comment: str):
        self.buffer += self.INDENTS + self.COMMENT_PROMPT + " " + comment + "\n"

    def close(self) -> str:
        return self.buffer
