"""
The TAC generation phase: translate the abstract syntax tree into three-address code.

You need to focus on two classes: TACFuncEmitter and TACGen.
TACGen is an AST visitor and performs high-level transformations.
TACFuncEmitter handles low-level TAC generation.
"""


from frontend.ast import node
from frontend.ast.tree import *
from frontend.ast.visitor import Visitor
from frontend.symbol.varsymbol import VarSymbol
from frontend.type.array import ArrayType
from utils.tac import tacinstr
from utils.tac.tacprog import TACProg, TACFunc, TACBlock
from utils.tac.reg import Temp
from utils.label.funclabel import FuncLabel
from utils.label.blocklabel import BlockLabel


# A global label manager (just a counter)
class LabelManager:
    def __init__(self) -> None:
        self.num_labels = 0

    def new_label(self) -> str:
        self.num_labels += 1
        return ".L" + str(self.num_labels)


# Translates a minidecaf function into low-level TAC function
# NOTE: this class was previously called `FuncVisitor`
class TACFuncEmitter:
    def __init__(self, label_man: LabelManager) -> None:
        # label & code block management
        self.label_man = label_man
        self.cur_block: TACBlock | None = None
        self.code_blocks: list[TACBlock] = []

        # temporary variables allocation
        self.num_temp_vars = 0

        # labels for break/continue
        self.break_labels = []
        self.continue_labels = []

    # Obtain a fresh new label (for branching).
    def new_label(self) -> str:
        if self.cur_block is not None:
            # close existing block
            self.code_blocks.append(self.cur_block)
        label = self.label_man.new_label()
        self.cur_block = TACBlock(label)
        return label

    # Obtain a fresh new temporary variable.
    def new_temp(self) -> Temp:
        self.num_temp_vars += 1
        return Temp(self.num_temp_vars)

    # Open a new loop. (for break/continue statements)
    def open_loop(self, break_label: str, continue_label: str) -> None:
        self.break_labels.append(break_label)
        self.continue_labels.append(continue_label)

    # Close current loop.
    def close_loop(self) -> None:
        self.break_labels.pop()
        self.continue_labels.pop()

    # Get the label for 'break' of current loop.
    def cur_break_label(self) -> str:
        return self.break_labels[-1]

    # Get the label for 'continue' of current loop.
    def cur_continue_label(self) -> str:
        return self.continue_labels[-1]

    # Append new TAC instruction.
    def emit(self, instr: tacinstr.TACInstr) -> None:
        if self.cur_block is None:
            self.cur_block = TACBlock(self.label_man.new_label())
        self.cur_block.add(instr)

    # Methods below process TAC code generation.

    # NOTE: assignment is for non-SSA
    def emit_assignment(self, dst: Temp, src: Temp) -> Temp:
        self.emit(tacinstr.Assign(dst, src))
        return dst

    def emit_load_imm(self, value: int) -> Temp:
        dst = self.new_temp()
        self.emit(tacinstr.LoadImm4(dst, value))
        return dst

    def emit_unary(self, op: tacinstr.UnaryOp, src: Temp) -> Temp:
        dst = self.new_temp()
        self.emit(tacinstr.Unary(op, dst, src))
        return dst

    def emit_inplace_unary(self, op: tacinstr.UnaryOp, dst: Temp) -> None:
        self.emit(tacinstr.Unary(op, dst, dst))

    def emit_binary(self, op: tacinstr.BinaryOp, lhs: Temp, rhs: Temp) -> Temp:
        dst = self.new_temp()
        self.emit(tacinstr.Binary(op, dst, lhs, rhs))
        return dst

    def emit_inplace_binary(self, op: tacinstr.UnaryOp, dst: Temp, src: Temp) -> None:
        self.emit(tacinstr.Binary(op, dst, dst, src))

    def emit_branch(self, target: str) -> None:
        self.emit(tacinstr.Branch(BlockLabel(target)))

    def emit_cond_branch(
        self, op: tacinstr.CondBranchOp, cond: Temp, target: str
    ) -> None:
        self.emit(tacinstr.CondBranch(op, cond, BlockLabel(target)))

    def emit_return(self, value: Temp | None) -> None:
        self.emit(tacinstr.Return(value))

    # Finish code generation and return TAC function
    def finish(self, func_name: str) -> TACFunc:
        last_block = self.cur_block
        if last_block is not None:
            terminator = last_block.terminator()
            if not isinstance(terminator, tacinstr.Return):
                last_block.add(tacinstr.Return())
            self.code_blocks.append(last_block)

        # NOTE: compatibility code here
        # TODO: remove
        tac_fn = TACFunc(FuncLabel(func_name), -1)
        tac_fn.tempUsed = self.num_temp_vars
        for block in self.code_blocks:
            tac_fn.add(tacinstr.Mark(BlockLabel(block.label)))
            for instr in block:
                tac_fn.add(instr)
        return tac_fn


class TACGen(Visitor[TACFuncEmitter, None]):
    def __init__(self) -> None:
        self.label_man = LabelManager()

    # Entry of this phase
    # TODO
    def transform(self, program: Program) -> TACProg:
        # handle global variables here if necessary.

        tac_funcs = []
        for func_name, function in program.functions().items():
            emitter = TACFuncEmitter(self.label_man)
            function.body.accept(self, emitter)
            tac_funcs.append(emitter.finish(func_name))
        return TACProg(tac_funcs)

    def visit_block(self, block: Block, mv: TACFuncEmitter) -> None:
        for child in block:
            child.accept(self, mv)

    def visit_return(self, stmt: Return, mv: TACFuncEmitter) -> None:
        stmt.expr.accept(self, mv)
        mv.emit_return(stmt.expr.getattr("val"))

    def visit_break(self, stmt: Break, mv: TACFuncEmitter) -> None:
        mv.emit_branch(mv.cur_break_label())

    def visit_identifier(self, ident: Identifier, mv: TACFuncEmitter) -> None:
        """
        1. Set the 'val' attribute of ident as the temp variable of the 'symbol' attribute of ident.
        """
        pass

    def visit_declaration(self, decl: Declaration, mv: TACFuncEmitter) -> None:
        """
        1. Get the 'symbol' attribute of decl.
        2. Use mv.freshTemp to get a new temp variable for this symbol.
        3. If the declaration has an initial value, use mv.visitAssignment to set it.
        """
        pass

    def visit_assignment(self, expr: Assignment, mv: TACFuncEmitter) -> None:
        """
        1. Visit the right hand side of expr, and get the temp variable of left hand side.
        2. Use mv.visitAssignment to emit an assignment instruction.
        3. Set the 'val' attribute of expr as the value of assignment instruction.
        """
        pass

    def visit_if(self, stmt: If, mv: TACFuncEmitter) -> None:
        """
        stmt.cond.accept(self, mv)

        if stmt.otherwise is NULL:
            skipLabel = mv.freshLabel()
            mv.visitCondBranch(
                tacinstr.CondBranchOp.BEQ, stmt.cond.getattr("val"), skipLabel
            )
            stmt.then.accept(self, mv)
            mv.visitLabel(skipLabel)
        else:
            skipLabel = mv.freshLabel()
            exitLabel = mv.freshLabel()
            mv.visitCondBranch(
                tacinstr.CondBranchOp.BEQ, stmt.cond.getattr("val"), skipLabel
            )
            stmt.then.accept(self, mv)
            mv.visitBranch(exitLabel)
            mv.visitLabel(skipLabel)
            stmt.otherwise.accept(self, mv)
            mv.visitLabel(exitLabel)
        """

    def visit_while(self, stmt: While, mv: TACFuncEmitter) -> None:
        """
        beginLabel = mv.freshLabel()
        loopLabel = mv.freshLabel()
        breakLabel = mv.freshLabel()
        mv.openLoop(breakLabel, loopLabel)

        mv.visitLabel(beginLabel)
        stmt.cond.accept(self, mv)
        mv.visitCondBranch(
            tacinstr.CondBranchOp.BEQ, stmt.cond.getattr("val"), breakLabel
        )

        stmt.body.accept(self, mv)
        mv.visitLabel(loopLabel)
        mv.visitBranch(beginLabel)
        mv.visitLabel(breakLabel)
        mv.closeLoop()
        """

    def visit_unary(self, expr: Unary, mv: TACFuncEmitter) -> None:
        expr.operand.accept(self, mv)

        op = {
            node.UnaryOp.Neg: tacinstr.UnaryOp.NEG,
            node.UnaryOp.BitNot: tacinstr.UnaryOp.NOT,
            node.UnaryOp.LogicNot: tacinstr.UnaryOp.SEQZ,
            # You can add unary operations here.
        }[expr.op]
        expr.setattr("val", mv.emit_unary(op, expr.operand.getattr("val")))

    def visit_binary(self, expr: Binary, mv: TACFuncEmitter) -> None:
        expr.lhs.accept(self, mv)
        expr.rhs.accept(self, mv)

        op = {
            node.BinaryOp.Add: tacinstr.BinaryOp.ADD,
            # You can add binary operations here.
        }[expr.op]
        expr.setattr(
            "val", mv.emit_binary(op, expr.lhs.getattr("val"), expr.rhs.getattr("val"))
        )

    def visit_cond_expr(self, expr: ConditionExpression, mv: TACFuncEmitter) -> None:
        """
        1. Refer to the implementation of visitIf and visitBinary.
        """
        pass

    def visit_int_literal(self, expr: IntLiteral, mv: TACFuncEmitter) -> None:
        expr.setattr("val", mv.emit_load_imm(expr.value))
