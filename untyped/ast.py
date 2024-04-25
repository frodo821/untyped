from typing import TypeAlias


class ASTNode:

  def __init__(self, file: str, line: int, col: int):
    self.file = file
    self.line = line
    self.col = col

  def __repr__(self):
    return str(self)


Expression: TypeAlias = 'Identifier | Apply | Lambda | Parentheses'


class Identifier(ASTNode):

  __match_args__ = ('file', 'line', 'col', 'name')

  def __init__(self, file: str, line: int, col: int, name: str):
    super().__init__(file, line, col)
    self.name = name

  def __str__(self):
    return self.name

  def __hash__(self):
    return hash(self.name)

  def __eq__(self, other):
    return isinstance(other, Identifier) and self.name == other.name


class Lambda(ASTNode):

  __match_args__ = ('file', 'line', 'col', 'param', 'body')

  def __init__(self, file: str, line: int, col: int, param: Identifier, body: Expression):
    super().__init__(file, line, col)
    self.param = param
    self.body = body

  def __str__(self):
    return f"{self.param}.{self.body}"


class Parentheses(ASTNode):

  __match_args__ = ('file', 'line', 'col', 'expr')

  def __init__(self, file: str, line: int, col: int, expr: Expression):
    super().__init__(file, line, col)
    self.expr = expr

  def __str__(self):
    return f"({self.expr})"


class Apply(ASTNode):

  __match_args__ = ('file', 'line', 'col', 'func', 'applicant')

  def __init__(self, file: str, line: int, col: int, func: Expression, applicant: Expression):
    super().__init__(file, line, col)
    self.func = func
    self.applicant = applicant

  def __str__(self):
    if isinstance(self.func, (Lambda)):
      return f"({self.func}) {self.applicant}"
    return f"{self.func} {self.applicant}"


class Binding(ASTNode):

  __match_args__ = ('file', 'line', 'col', 'name', 'expr')

  def __init__(self, file: str, line: int, col: int, name: Identifier, expr: Expression):
    super().__init__(file, line, col)
    self.name = name
    self.expr = expr

  def __str__(self):
    return f"let {self.name} = {self.expr}"


class Program(ASTNode):

  __match_args__ = ('file', 'line', 'col', 'bindings', 'expr')

  def __init__(self, file: str, line: int, col: int, bindings: list[Binding], expr: Expression):
    super().__init__(file, line, col)
    self.bindings = bindings
    self.expr = expr

  def __str__(self):
    return f"{str(self.expr)}\nwhere\n{chr(0x0A).join(map(str, self.bindings))}"


def dump_ast(ast: ASTNode, *, depth = 0):
  match ast:
    case Identifier(f, l, c, name):
      print(f"{'  ' * depth}Identifier {name} ({f}:{l}:{c})")
    case Lambda(f, l, c, param, body):
      print(f"{'  ' * depth}Lambda ({f}:{l}:{c})")
      dump_ast(param, depth=depth+1)
      dump_ast(body, depth=depth+1)
    case Parentheses(f, l, c, expr):
      print(f"{'  ' * depth}Parentheses ({f}:{l}:{c})")
      dump_ast(expr, depth=depth+1)
    case Apply(f, l, c, func, applicant):
      print(f"{'  ' * depth}Apply ({f}:{l}:{c})")
      dump_ast(func, depth=depth+1)
      dump_ast(applicant, depth=depth+1)
    case Binding(f, l, c, name, expr):
      print(f"{'  ' * depth}Binding ({f}:{l}:{c})")
      dump_ast(name, depth=depth+1)
      dump_ast(expr, depth=depth+1)
    case Program(f, l, c, bindings, expr):
      print(f"{'  ' * depth}Program ({f}:{l}:{c})")
      for binding in bindings:
        dump_ast(binding, depth=depth+1)
      dump_ast(expr, depth=depth+1)
