from typing import TypeVar
from untyped.ast import Apply, Expression, Identifier, Lambda, Parentheses

T = TypeVar('T', bound=Expression)

def alpha_convert(expr: T, old: Identifier, new: Identifier) -> T:
  match expr:
    case Identifier(_, _, _, _) as ident:
      return new if ident == old else ident  # type: ignore
    case Lambda(_, _, _, param, body):
      if param == old:
        return expr
      return Lambda(expr.file, expr.line, expr.col, param, alpha_convert(body, old, new))  # type: ignore
    case Parentheses(_, _, _, e):
      return Parentheses(e.file, e.line, e.col, alpha_convert(e, old, new))  # type: ignore
    case Apply(_, _, _, func, applicant):
      return Apply(expr.file, expr.line, expr.col, alpha_convert(func, old, new), alpha_convert(applicant, old, new))  # type: ignore


def unique_ident(expr: T, known: dict[Identifier, int] | None = None) -> T:
  known = known or {}

  match expr:
    case Lambda(_, _, _, param, body):
      if param in known:
        known[param] += 1
        new = Identifier(param.file, param.line, param.col, f"{param.name}${known[param]}")

        return Lambda(expr.file, expr.line, expr.col, new, alpha_convert(body, param, new))  # type: ignore
      known[param] = 0
    case Parentheses(_, _, _, e):
      return Parentheses(e.file, e.line, e.col, unique_ident(e, known.copy()))  # type: ignore
    case Apply(_, _, _, func, applicant):
      return Apply(expr.file, expr.line, expr.col, unique_ident(func, known.copy()), unique_ident(applicant, known.copy()))  # type: ignore
  return expr


def ununique_ident(expr: T) -> T:
  def _walk(expr: T) -> T:
    match expr:
      case Identifier(_, _, _, name):
        return Identifier(expr.file, expr.line, expr.col, name.split('$')[0]) # type: ignore
      case Lambda(_, _, _, param, body):
        return Lambda(expr.file, expr.line, expr.col, _walk(param), _walk(body)) # type: ignore
      case Parentheses(_, _, _, e):
        return Parentheses(e.file, e.line, e.col, _walk(e)) # type: ignore
      case Apply(_, _, _, func, applicant):
        return Apply(expr.file, expr.line, expr.col, _walk(func), _walk(applicant)) # type: ignore

  return _walk(expr)


def apply(func: Lambda, applicant: Expression) -> Expression:
  func = unique_ident(func)
  param = func.param

  def _walk(expr: Expression) -> Expression:
    match expr:
      case Identifier(_, _, _, _) as ident:
        return applicant if ident == param else ident
      case Lambda(_, _, _, _, _):
        if param == expr.param:
          return expr
        return Lambda(expr.file, expr.line, expr.col, expr.param, _walk(expr.body))
      case Parentheses(_, _, _, e):
        return Parentheses(e.file, e.line, e.col, _walk(e))
      case Apply(_, _, _, f, a):
        return Apply(expr.file, expr.line, expr.col, _walk(f), _walk(a))

  return ununique_ident(_walk(func.body))


def eval(expr: Expression) -> Expression:
  match expr:
    case Identifier(_, _, _, _):
      return expr
    case Lambda(_, _, _, _, _):
      return expr
    case Parentheses(_, _, _, e):
      return eval(e)
    case Apply(_, _, _, func, applicant):
      func = eval(func)
      applicant = eval(applicant)

      if isinstance(func, Lambda):
        return eval(apply(func, applicant))
      return Apply(expr.file, expr.line, expr.col, func, applicant)
