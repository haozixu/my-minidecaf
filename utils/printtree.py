from frontend.ast.node import Node


class TreePrinter:
    l = "["
    r = "]"
    lr = l + r

    def __init__(self, indent_len=4) -> None:
        self.indent_len = indent_len
        self.indent_num = 0

    def print(self, element) -> None:
        if element is None:
            self.print_line("<None: here is a bug>")

        elif isinstance(element, Node):
            if element.is_leaf():
                self.print_line(str(element))
                return

            if len(element) == 0:
                self.print_line(f"{element.name} {self.lr}")
                return

            self.print_line(f"{element.name} {self.l}")
            self.inc_indent()
            for it in element:
                self.print(it)
            self.dec_indent()
            self.print_line(self.r)

        elif isinstance(element, list):
            self.print_line("List")
            self.inc_indent()
            if len(element) == 0:
                self.print_line("<empty>")
            else:
                for it in element:
                    self.print(it)
            self.dec_indent()

        else:
            self.print_line(str(element))

    def output_indent(self) -> None:
        if self.indent_num > 0:
            print(" " * self.indent_len * self.indent_num, end="")

    def print_line(self, s: str) -> None:
        self.output_indent()
        print(s)

    def inc_indent(self) -> None:
        self.indent_num += 1

    def dec_indent(self) -> None:
        self.indent_num -= 1
