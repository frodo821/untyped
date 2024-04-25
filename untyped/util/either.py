from dataclasses import dataclass
from typing import Generic, TypeAlias, TypeGuard, TypeVar

T = TypeVar('T')
E = TypeVar('E')

@dataclass(frozen=True, repr=False)
class Ok(Generic[T]):
  value: T

  def __repr__(self):
    return f"Ok({self.value})"

  def __str__(self):
    return f"Ok({self.value})"


@dataclass(frozen=True, repr=False)
class Err(Generic[E]):
  value: E

  def __repr__(self):
    return f"Err({self.value})"

  def __str__(self):
    return f"Err({self.value})"


Either: TypeAlias = Ok[T] | Err[E]
