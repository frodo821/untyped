from dataclasses import dataclass


@dataclass
class UntypedError(Exception):
  message: str
  file: str
  line: int
  col: int
