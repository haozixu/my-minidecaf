"""
Module that defines the base type of visitor.
"""


from __future__ import annotations

from typing import Callable, Protocol, Sequence, TypeVar

from .node import *
from .tree import *

T = TypeVar("T", covariant=True)
U = TypeVar("U", covariant=True)


def accept(visitor: Visitor[T, U], ctx: T) -> Callable[[Node], Optional[U]]:
    return lambda node: node.accept(visitor, ctx)


class Visitor(Protocol[T, U]):  # type: ignore
    def visit_other(self, node: Node, ctx: T) -> None:
        return None

    def visit_null(self, that: NullType, ctx: T) -> Optional[U]:
        return self.visit_other(that, ctx)

    def visit_program(self, that: Program, ctx: T) -> Optional[Sequence[Optional[U]]]:
        return self.visit_other(that, ctx)

    def visit_block(self, that: Block, ctx: T) -> Optional[Sequence[Optional[U]]]:
        return self.visit_other(that, ctx)

    def visit_function(self, that: Function, ctx: T) -> Optional[U]:
        return self.visit_other(that, ctx)

    def visit_if(self, that: If, ctx: T) -> Optional[U]:
        return self.visit_other(that, ctx)

    def visit_return(self, that: Return, ctx: T) -> Optional[U]:
        return self.visit_other(that, ctx)

    def visit_while(self, that: While, ctx: T) -> Optional[U]:
        return self.visit_other(that, ctx)

    def visit_break(self, that: Break, ctx: T) -> Optional[U]:
        return self.visit_other(that, ctx)

    def visit_declaration(self, that: Declaration, ctx: T) -> Optional[U]:
        return self.visit_other(that, ctx)

    def visit_unary(self, that: Unary, ctx: T) -> Optional[U]:
        return self.visit_other(that, ctx)

    def visit_binary(self, that: Binary, ctx: T) -> Optional[U]:
        return self.visit_other(that, ctx)

    def visit_assignment(self, that: Assignment, ctx: T) -> Optional[U]:
        """
        ## ! Note that the default behavior is `visit_binary`, not `visit_other`
        """
        return self.visit_binary(that, ctx)

    def visit_cond_expr(self, that: ConditionExpression, ctx: T) -> Optional[U]:
        return self.visit_other(that, ctx)

    def visit_identifier(self, that: Identifier, ctx: T) -> Optional[U]:
        return self.visit_other(that, ctx)

    def visit_int_literal(self, that: IntLiteral, ctx: T) -> Optional[U]:
        return self.visit_other(that, ctx)

    def visit_tint(self, that: TInt, ctx: T) -> Optional[U]:
        return self.visit_other(that, ctx)


class RecursiveVisitor(Visitor[T, U]):
    def visit_other(self, node: Node, ctx: T) -> Optional[Sequence[Optional[U]]]:
        ret = tuple(map(accept(self, ctx), node))
        return ret if ret and ret.count(None) == len(ret) else None
