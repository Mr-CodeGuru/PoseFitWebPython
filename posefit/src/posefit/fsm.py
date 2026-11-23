"""Finite-state machine condition parsing, expression AST, and state transitions.

Finite state machine condition parser and transition engine.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Any

from posefit.config import FLOAT_EQUALITY_EPSILON

# ============================================================================
# Evaluation Context & Variable Resolver
# ============================================================================

class EvaluationContext:
    """Provides variable resolution for condition expressions.

    Context holding kinematic state for condition evaluation.
    """

    __slots__ = ("angles", "coords", "primary_angle_name")

    def __init__(
        self,
        angles: dict[str, float] | None = None,
        coords: dict[str, tuple[int, int]] | None = None,
        primary_angle_name: str | None = None,
    ) -> None:
        self.angles: dict[str, float] = angles or {}
        self.coords: dict[str, tuple[int, int]] = coords or {}
        self.primary_angle_name: str | None = primary_angle_name

    def with_angle(self, name: str, value: float) -> EvaluationContext:
        self.angles[name] = value
        return self

    def with_primary_angle(self, name: str, value: float) -> EvaluationContext:
        self.angles[name] = value
        self.primary_angle_name = name
        return self

    def with_coord(self, name: str, x: int, y: int) -> EvaluationContext:
        self.coords[name] = (x, y)
        return self

    def get_var(self, name: str) -> float | None:
        """Resolves variable name to float value from context."""
        # 1. Direct angle match
        if name in self.angles:
            return self.angles[name]

        # 2. "angle" alias resolution
        if name == "angle":
            if self.primary_angle_name and self.primary_angle_name in self.angles:
                return self.angles[self.primary_angle_name]
            if "primary" in self.angles:
                return self.angles["primary"]
            if "left" in self.angles:
                return self.angles["left"]
            if "right" in self.angles:
                return self.angles["right"]
            return None

        # 3. Name ends with "_angle" (e.g. "body_line_angle" or "primary_angle")
        if name.endswith("_angle"):
            base = name[:-6]
            if base in self.angles:
                return self.angles[base]
            if name in self.angles:
                return self.angles[name]

        # 4. Name ends with "_x"
        if name.endswith("_x"):
            base = name[:-2]
            if base in self.coords:
                return float(self.coords[base][0])

        # 5. Name ends with "_y"
        if name.endswith("_y"):
            base = name[:-2]
            if base in self.coords:
                return float(self.coords[base][1])

        return None


# ============================================================================
# Arithmetic Expression AST
# ============================================================================

class Expr(ABC):
    @abstractmethod
    def evaluate(self, ctx: EvaluationContext) -> float:
        pass


@dataclass(slots=True, frozen=True)
class NumberExpr(Expr):
    val: float

    def evaluate(self, ctx: EvaluationContext) -> float:
        return self.val


@dataclass(slots=True, frozen=True)
class VarExpr(Expr):
    name: str

    def evaluate(self, ctx: EvaluationContext) -> float:
        val = ctx.get_var(self.name)
        if val is None:
            raise ValueError(f"Variable '{self.name}' not found in evaluation context")
        return val


@dataclass(slots=True, frozen=True)
class AddExpr(Expr):
    lhs: Expr
    rhs: Expr

    def evaluate(self, ctx: EvaluationContext) -> float:
        return self.lhs.evaluate(ctx) + self.rhs.evaluate(ctx)


@dataclass(slots=True, frozen=True)
class SubExpr(Expr):
    lhs: Expr
    rhs: Expr

    def evaluate(self, ctx: EvaluationContext) -> float:
        return self.lhs.evaluate(ctx) - self.rhs.evaluate(ctx)


@dataclass(slots=True, frozen=True)
class AbsExpr(Expr):
    inner: Expr

    def evaluate(self, ctx: EvaluationContext) -> float:
        return abs(self.inner.evaluate(ctx))


# ============================================================================
# Condition AST
# ============================================================================

class CompOp(Enum):
    LT = "<"
    LTE = "<="
    GT = ">"
    GTE = ">="
    EQ = "=="
    NEQ = "!="


class Condition(ABC):
    @abstractmethod
    def evaluate(self, ctx: EvaluationContext) -> bool:
        pass


@dataclass(slots=True, frozen=True)
class AlwaysCondition(Condition):
    val: bool

    def evaluate(self, ctx: EvaluationContext) -> bool:
        return self.val


@dataclass(slots=True, frozen=True)
class ComparisonCondition(Condition):
    left: Expr
    op: CompOp
    right: Expr

    def evaluate(self, ctx: EvaluationContext) -> bool:
        l_val = self.left.evaluate(ctx)
        r_val = self.right.evaluate(ctx)
        if self.op == CompOp.LT:
            return l_val < r_val
        if self.op == CompOp.LTE:
            return l_val <= r_val
        if self.op == CompOp.GT:
            return l_val > r_val
        if self.op == CompOp.GTE:
            return l_val >= r_val
        if self.op == CompOp.EQ:
            return abs(l_val - r_val) < FLOAT_EQUALITY_EPSILON
        if self.op == CompOp.NEQ:
            return abs(l_val - r_val) >= FLOAT_EQUALITY_EPSILON
        return False


@dataclass(slots=True, frozen=True)
class AndCondition(Condition):
    conds: tuple[Condition, ...]

    def evaluate(self, ctx: EvaluationContext) -> bool:
        for c in self.conds:
            if not c.evaluate(ctx):
                return False
        return True


@dataclass(slots=True, frozen=True)
class OrCondition(Condition):
    conds: tuple[Condition, ...]

    def evaluate(self, ctx: EvaluationContext) -> bool:
        for c in self.conds:
            if c.evaluate(ctx):
                return True
        return False


@dataclass(slots=True, frozen=True)
class NotCondition(Condition):
    inner: Condition

    def evaluate(self, ctx: EvaluationContext) -> bool:
        return not self.inner.evaluate(ctx)


# ============================================================================
# Safe Recursive Descent Condition Parser
# ============================================================================

class TokenType(Enum):
    NUMBER = "NUMBER"
    IDENT = "IDENT"
    LT = "<"
    LTE = "<="
    GT = ">"
    GTE = ">="
    EQ = "=="
    NEQ = "!="
    AND = "and"
    OR = "or"
    NOT = "not"
    PLUS = "+"
    MINUS = "-"
    LPAREN = "("
    RPAREN = ")"
    ABS = "abs"
    TRUE = "true"
    FALSE = "false"


@dataclass(slots=True, frozen=True)
class Token:
    kind: TokenType
    value: Any = None


class ConditionParser:
    """Tokenizer and recursive descent parser for boolean state conditions."""

    _TOKEN_RE = re.compile(
        r"""
        (?P<NUMBER>\d+(?:\.\d+)?)
        |(?P<LTE><=)
        |(?P<GTE>>=)
        |(?P<EQ>==)
        |(?P<NEQ>!=)
        |(?P<LT><)
        |(?P<GT>>)
        |(?P<PLUS>\+)
        |(?P<MINUS>-)
        |(?P<LPAREN>\()
        |(?P<RPAREN>\))
        |(?P<IDENT>[a-zA-Z_]\w*)
        |(?P<WS>\s+)
        """,
        re.VERBOSE,
    )

    @classmethod
    def tokenize(cls, text: str) -> list[Token]:
        tokens: list[Token] = []
        pos = 0
        while pos < len(text):
            m = cls._TOKEN_RE.match(text, pos)
            if not m:
                raise ValueError(f"Unexpected character '{text[pos]}' in condition: {text}")
            pos = m.end()
            kind_str = m.lastgroup
            val = m.group()

            if kind_str == "WS":
                continue
            if kind_str == "NUMBER":
                tokens.append(Token(TokenType.NUMBER, float(val)))
            elif kind_str == "IDENT":
                low = val.lower()
                if low == "and":
                    tokens.append(Token(TokenType.AND))
                elif low == "or":
                    tokens.append(Token(TokenType.OR))
                elif low == "not":
                    tokens.append(Token(TokenType.NOT))
                elif low == "abs":
                    tokens.append(Token(TokenType.ABS))
                elif low in ("true", "1"):
                    tokens.append(Token(TokenType.TRUE))
                elif low in ("false", "0"):
                    tokens.append(Token(TokenType.FALSE))
                else:
                    tokens.append(Token(TokenType.IDENT, val))
            elif kind_str == "LT":
                tokens.append(Token(TokenType.LT))
            elif kind_str == "LTE":
                tokens.append(Token(TokenType.LTE))
            elif kind_str == "GT":
                tokens.append(Token(TokenType.GT))
            elif kind_str == "GTE":
                tokens.append(Token(TokenType.GTE))
            elif kind_str == "EQ":
                tokens.append(Token(TokenType.EQ))
            elif kind_str == "NEQ":
                tokens.append(Token(TokenType.NEQ))
            elif kind_str == "PLUS":
                tokens.append(Token(TokenType.PLUS))
            elif kind_str == "MINUS":
                tokens.append(Token(TokenType.MINUS))
            elif kind_str == "LPAREN":
                tokens.append(Token(TokenType.LPAREN))
            elif kind_str == "RPAREN":
                tokens.append(Token(TokenType.RPAREN))

        return tokens

    @classmethod
    def parse_str(cls, input_str: str) -> Condition:
        trimmed = input_str.strip()
        if not trimmed or trimmed.lower() == "true":
            return AlwaysCondition(True)
        if trimmed.lower() == "false":
            return AlwaysCondition(False)

        tokens = cls.tokenize(trimmed)
        pos = 0
        cond, pos = cls._parse_or(tokens, pos)
        if pos < len(tokens):
            raise ValueError(f"Unexpected trailing tokens in '{input_str}' at token {tokens[pos]}")
        return cond

    @classmethod
    def _parse_or(cls, tokens: list[Token], pos: int) -> tuple[Condition, int]:
        left, pos = cls._parse_and(tokens, pos)
        or_list = [left]
        while pos < len(tokens) and tokens[pos].kind == TokenType.OR:
            pos += 1
            right, pos = cls._parse_and(tokens, pos)
            or_list.append(right)
        if len(or_list) == 1:
            return or_list[0], pos
        return OrCondition(tuple(or_list)), pos

    @classmethod
    def _parse_and(cls, tokens: list[Token], pos: int) -> tuple[Condition, int]:
        left, pos = cls._parse_not(tokens, pos)
        and_list = [left]
        while pos < len(tokens) and tokens[pos].kind == TokenType.AND:
            pos += 1
            right, pos = cls._parse_not(tokens, pos)
            and_list.append(right)
        if len(and_list) == 1:
            return and_list[0], pos
        return AndCondition(tuple(and_list)), pos

    @classmethod
    def _parse_not(cls, tokens: list[Token], pos: int) -> tuple[Condition, int]:
        if pos < len(tokens) and tokens[pos].kind == TokenType.NOT:
            pos += 1
            inner, pos = cls._parse_not(tokens, pos)
            return NotCondition(inner), pos
        return cls._parse_primary_cond(tokens, pos)

    @classmethod
    def _parse_primary_cond(cls, tokens: list[Token], pos: int) -> tuple[Condition, int]:
        if pos < len(tokens):
            if tokens[pos].kind == TokenType.TRUE:
                return AlwaysCondition(True), pos + 1
            if tokens[pos].kind == TokenType.FALSE:
                return AlwaysCondition(False), pos + 1
            if tokens[pos].kind == TokenType.LPAREN:
                save = pos
                pos += 1
                try:
                    cond, pos = cls._parse_or(tokens, pos)
                    if pos < len(tokens) and tokens[pos].kind == TokenType.RPAREN:
                        pos += 1
                        # Check if followed by comparison operator
                        if pos < len(tokens) and tokens[pos].kind in (
                            TokenType.LT, TokenType.LTE, TokenType.GT,
                            TokenType.GTE, TokenType.EQ, TokenType.NEQ
                        ):
                            pos = save  # backtrack, parse as arithmetic expr
                        else:
                            return cond, pos
                    else:
                        pos = save
                except Exception:
                    pos = save

        left_expr, pos = cls._parse_expr(tokens, pos)
        if pos >= len(tokens):
            raise ValueError("Expected comparison operator after expression")

        op_token = tokens[pos]
        comp_map = {
            TokenType.LT: CompOp.LT,
            TokenType.LTE: CompOp.LTE,
            TokenType.GT: CompOp.GT,
            TokenType.GTE: CompOp.GTE,
            TokenType.EQ: CompOp.EQ,
            TokenType.NEQ: CompOp.NEQ,
        }
        if op_token.kind not in comp_map:
            raise ValueError(f"Expected comparison operator, found {op_token.kind}")
        op = comp_map[op_token.kind]
        pos += 1

        right_expr, pos = cls._parse_expr(tokens, pos)

        # Support Python chained comparisons: e.g. "47 < angle <= 155"
        if pos < len(tokens) and tokens[pos].kind in comp_map:
            op2 = comp_map[tokens[pos].kind]
            pos += 1
            right2_expr, pos = cls._parse_expr(tokens, pos)
            c1 = ComparisonCondition(left=left_expr, op=op, right=right_expr)
            c2 = ComparisonCondition(left=right_expr, op=op2, right=right2_expr)
            return AndCondition((c1, c2)), pos

        return ComparisonCondition(left=left_expr, op=op, right=right_expr), pos

    @classmethod
    def _parse_expr(cls, tokens: list[Token], pos: int) -> tuple[Expr, int]:
        left, pos = cls._parse_term(tokens, pos)
        while pos < len(tokens):
            if tokens[pos].kind == TokenType.PLUS:
                pos += 1
                right, pos = cls._parse_term(tokens, pos)
                left = AddExpr(left, right)
            elif tokens[pos].kind == TokenType.MINUS:
                pos += 1
                right, pos = cls._parse_term(tokens, pos)
                left = SubExpr(left, right)
            else:
                break
        return left, pos

    @classmethod
    def _parse_term(cls, tokens: list[Token], pos: int) -> tuple[Expr, int]:
        if pos >= len(tokens):
            raise ValueError("Unexpected end of input in arithmetic expression")

        tok = tokens[pos]
        if tok.kind == TokenType.NUMBER:
            return NumberExpr(tok.value), pos + 1
        if tok.kind == TokenType.IDENT:
            return VarExpr(tok.value), pos + 1
        if tok.kind == TokenType.ABS:
            pos += 1
            if pos < len(tokens) and tokens[pos].kind == TokenType.LPAREN:
                pos += 1
                inner, pos = cls._parse_expr(tokens, pos)
                if pos < len(tokens) and tokens[pos].kind == TokenType.RPAREN:
                    return AbsExpr(inner), pos + 1
                raise ValueError("Expected closing ')' after abs(...)")
            raise ValueError("Expected '(' after abs")
        if tok.kind == TokenType.LPAREN:
            pos += 1
            inner, pos = cls._parse_expr(tokens, pos)
            if pos < len(tokens) and tokens[pos].kind == TokenType.RPAREN:
                return inner, pos + 1
            raise ValueError("Expected closing ')' in expression")

        raise ValueError(f"Unexpected token in expression: {tok}")


# ============================================================================
# State Machine
# ============================================================================

@dataclass(slots=True)
class StateDefinition:
    name: str
    condition_str: str
    condition: Condition


class StateMachine:
    """Deterministic finite state machine evaluating states in priority order."""

    __slots__ = ("state_order", "states", "current_state", "prev_state")

    def __init__(
        self,
        state_order: Sequence[str],
        states: dict[str, StateDefinition],
    ) -> None:
        self.state_order: list[str] = list(state_order)
        self.states: dict[str, StateDefinition] = states
        self.current_state: str | None = None
        self.prev_state: str | None = None

    def update(self, ctx: EvaluationContext) -> tuple[str | None, bool]:
        """Evaluates states in `state_order`.

        First state whose condition is True becomes current_state.
        Returns (current_state, state_changed).
        """
        for state_name in self.state_order:
            state_def = self.states.get(state_name)
            if state_def and state_def.condition.evaluate(ctx):
                state_changed = self.current_state != state_name
                if state_changed:
                    self.prev_state = self.current_state
                    self.current_state = state_name
                return self.current_state, state_changed

        return self.current_state, False

    def reset(self) -> None:
        self.current_state = None
        self.prev_state = None
