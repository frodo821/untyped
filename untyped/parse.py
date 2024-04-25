from enum import Enum, auto
from typing import Any, Callable

from untyped.ast import ASTNode, Apply, Binding, Expression, Identifier, Lambda, Parentheses, Program
from untyped.exc import UntypedError
from untyped.util.either import Either, Err, Ok


class TokenType(Enum):

  IDENTIFIER = auto()
  DOT = auto()
  EQUAL = auto()
  R_PAREN = auto()
  L_PAREN = auto()
  LET = auto()
  WHERE = auto()

  def expect(self, tokens: 'list[Token]', pos: int) -> Either['Token', UntypedError]:
    if not tokens[pos:]:
      return Err(UntypedError(f"Expected {self.name} but got EOF", tokens[pos-1].file, tokens[pos-1].line, tokens[pos-1].col))
    
    if tokens[pos].type != self:
      return Err(UntypedError(f"Expected {self.name} but got {tokens[pos].type.name}", tokens[pos].file, tokens[pos].line, tokens[pos].col))

    return Ok(tokens[pos])


class Token:

  def __init__(self, type: TokenType, value: str, file: str, line: int, col: int):
    self.type = type
    self.value = value
    self.file = file
    self.line = line
    self.col = col

  def __str__(self):
    return self.value

  def __repr__(self):
    return str(self)


def tokenize(file: str, code: str) -> list[Token]:
  tokens: list[Token] = []
  line, col, cons = 1, 0, 0

  for c in code:
    cons += 1
    col += 1

    if c == '\n':
      line += 1
      col = 0
      continue

    if c == ' ':
      continue

    if c == '.':
      tokens.append(Token(TokenType.DOT, c, file, line, col))
      continue

    if c == '=':
      tokens.append(Token(TokenType.EQUAL, c, file, line, col))
      continue

    if c == '(':
      tokens.append(Token(TokenType.L_PAREN, c, file, line, col))
      continue

    if c == ')':
      tokens.append(Token(TokenType.R_PAREN, c, file, line, col))
      continue

    if c == 'l' and code[cons:cons + 2] == 'et':
      tokens.append(Token(TokenType.LET, 'let', file, line, col))
      cons += 2
      col += 2
      continue

    if c == 'w' and code[cons:cons + 4] == 'here':
      tokens.append(Token(TokenType.WHERE, 'where', file, line, col))
      cons += 4
      col += 4
      continue

    if c in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_':
      start = cons - 1
      sc = col

      while col < len(code) and code[col] in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_':
        col += 1
        cons += 1

      tokens.append(Token(TokenType.IDENTIFIER, code[start:cons], file, line, sc))
      continue

    raise ValueError(f"Unexpected character '{c}' at {file}:{line}:{col}")

  return tokens


def parse_lambda(tokens: list[Token], pos: int) -> Either[tuple[Expression, int], UntypedError]:
  match TokenType.IDENTIFIER.expect(tokens, pos):
    case Err(_) as e:
      return e
    case Ok(token):
      param = Identifier(token.file, token.line, token.col, token.value)

  match TokenType.DOT.expect(tokens, pos + 1):
    case Err(_) as e:
      return e

  match parse_expr(tokens, pos + 2):
    case Err(_) as e:
      return e
    case Ok((expr, next)):
      return Ok((Lambda(tokens[pos].file, tokens[pos].line, tokens[pos].col, param, expr), next))


def parse_parentheses(tokens: list[Token], pos: int) -> Either[tuple[Expression, int], UntypedError]:
  match TokenType.L_PAREN.expect(tokens, pos):
    case Err(_) as e:
      return e

  match parse_expr(tokens, pos + 1):
    case Err(_) as e:
      return e
    case Ok((expr, next)):
      pass

  match TokenType.R_PAREN.expect(tokens, next):
    case Err(_) as e:
      return e
    case Ok(_):
      return Ok((Parentheses(tokens[pos].file, tokens[pos].line, tokens[pos].col, expr), next + 1))


def parse_apply(tokens: list[Token], pos: int) -> Either[tuple[Expression, int], UntypedError]:
  match parse_primal_expr(tokens, pos):
    case Err(_) as e:
      return e
    case Ok((func, next)):
      pass

  f = True

  while True:
    match parse_primal_expr(tokens, next):
      case Err(_) as e:
        if f:
          return e
        return Ok((func, next))
      case Ok((applicant, next)):
        func = Apply(tokens[pos].file, tokens[pos].line, tokens[pos].col, func, applicant)
    f = False


def parse_primal_expr(tokens: list[Token], pos: int) -> Either[tuple[Expression, int], UntypedError]:
  match parse_lambda(tokens, pos):
    case Ok((expr, next)):
      return Ok((expr, next))
    case Err(_) as e:
      pass

  match parse_parentheses(tokens, pos):
    case Ok((expr, next)):
      return Ok((expr, next))
    case Err(_) as e:
      pass

  match TokenType.IDENTIFIER.expect(tokens, pos):
    case Err(_) as e:
      return e
    case Ok(token):
      return Ok((Identifier(token.file, token.line, token.col, token.value), pos + 1))


def parse_expr(tokens: list[Token], pos: int) -> Either[tuple[Expression, int], UntypedError]:
  match parse_apply(tokens, pos):
    case Ok((expr, next)):
      return Ok((expr, next))
    case Err(_) as e:
      pass

  match parse_primal_expr(tokens, pos):
    case Ok((expr, next)):
      return Ok((expr, next))
    case Err(_) as e:
      return e


def parse_binding(tokens: list[Token], pos: int) -> Either[tuple[Binding, int], UntypedError]:
  match TokenType.LET.expect(tokens, pos):
    case Err(_) as e:
      return e

  match TokenType.IDENTIFIER.expect(tokens, pos):
    case Err(_) as e:
      return e
    case Ok(token):
      name = Identifier(token.file, token.line, token.col, token.value)

  match TokenType.EQUAL.expect(tokens, pos + 1):
    case Err(_) as e:
      return e

  match parse_expr(tokens, pos + 2):
    case Err(_) as e:
      return e
    case Ok((expr, next)):
      return Ok((Binding(tokens[pos].file, tokens[pos].line, tokens[pos].col, name, expr), next))


def parse(expr: str, file: str = '<stdin>') -> Expression:
  tokens = tokenize(file, expr)
  res = parse_expr(tokens, 0)

  match res:
    case Err(e):
      raise SyntaxError(f"{e.message} at line {e.line} column {e.col} in {e.file}")
    case Ok((exp, next)):
      if next != len(tokens):
        raise SyntaxError(
          f"Expected EOF but got {tokens[next].type.name} at line {tokens[next].line} column {tokens[next].col} in {tokens[next].file}"
        )
      return exp


def as_py_expr(expr: Expression) -> str:
  match expr:
    case Identifier(_, _, _, name):
      return name
    case Lambda(_, _, _, param, body):
      return f"lambda {as_py_expr(param)}: {as_py_expr(body)}"
    case Parentheses(_, _, _, e):
      return f"({as_py_expr(e)})"
    case Apply(_, _, _, func, applicant):
      return f"{as_py_expr(func)}({as_py_expr(applicant)})"
    case _:
      raise ValueError(f"Invalid expression {expr}")

def as_py_func(expr: Expression) -> Callable[[Any], Any]:
  return __builtins__['eval'](as_py_expr(expr))
