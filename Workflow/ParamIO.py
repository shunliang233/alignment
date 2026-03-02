#!/usr/bin/env python3
"""
Reader for Millepede-II parameters files (mp2par.txt / millepede.res).

File format:
  * ...          full-line comment (ignored)
  text ! ...     inline comment: everything after '!' is ignored
  Parameter      keyword marking the start of entries; lines before it are ignored
  <label>  <initial>  <presigma>  [extra columns ignored]
"""

from dataclasses import dataclass
from pathlib import Path

from Label import Label
from FixRule import FixRule


@dataclass
class Parameter:
    """A single entry in the parameters file."""
    label:    Label
    initial:  float
    presigma: float

    def __repr__(self) -> str:
        return f'Parameter({self.label!r}, {self.initial}, {self.presigma})'

    def __str__(self) -> str:
        return (
            f'    {self.label:<5}'
            f'    {self.initial:11.4e}'
            f'    {self.presigma:11.4e}'
        )


class ParamIO:
    """
    Reader for Millepede-II parameters file.

    Each non-comment, non-keyword line contains:
      <label>  <initial value>  <presigma>
    """

    # ---------------------------- Constructor ---------------------------- #

    def __init__(self, source: Path, target: Path):
        """
        Load a parameters file.

        Args:
            source: Path to the source file.
            target: Path to the output file.
        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If a data line cannot be parsed.
        """
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source}")
        self._source = source
        self._target = target
        self._parameters: list[Parameter] = self._parse(source)

    def _parse(self, source: Path) -> list[Parameter]:
        """Parse parameters from the source file."""
        entries = []
        seen: dict[Label, int] = {}  # label: lineno
        in_entries = False
        with open(source) as f:
            for lineno, raw in enumerate(f, start=1):
                line = raw.split('!')[0].strip()
                if not line or line.startswith('*'): # Comment line
                    continue
                if line == 'Parameter': # Keyword line
                    in_entries = True
                    continue
                if not in_entries: # Skip lines before 'Parameter'
                    continue
                parts = line.split()
                if len(parts) < 3:
                    raise ValueError(
                        f"{source}:{lineno}: expected at least 3 columns, "
                        f"got {len(parts)}: {line!r}.")
                try:
                    label    = Label(int(parts[0]))
                    initial  = float(parts[1])
                    presigma = float(parts[2])
                except (ValueError, TypeError) as e:
                    raise ValueError(f"{source}:{lineno}: {e}") from None
                if label in seen:
                    raise ValueError(
                        f"{source}:{lineno}: duplicate label {label}, "
                        f"first seen at line {seen[label]}.")
                seen[label] = lineno
                entries.append(Parameter(label, initial, presigma))
        return entries

    # -------------------------- Helper Methods -------------------------- #

    @property
    def parameters(self) -> list[Parameter]:
        """All parsed parameters in file order."""
        return self._parameters

    def __len__(self) -> int:
        return len(self._parameters)

    def __iter__(self):
        return iter(self._parameters)
    
    def __contains__(self, label_int: int) -> bool:
        return any(param.label == label_int for param in self._parameters)

    def __getitem__(self, label_int: int) -> Parameter:
        """
        Look up a parameter by integer label.

        Raises:
            KeyError: If the label is not found.
        """
        for param in self._parameters:
            if param.label == label_int:
                return param
        raise KeyError(f"Label {label_int} not found in {self._source}")

    def __setitem__(self, label_int: int, values: tuple[float, float]) -> None:
        """
        Modify initial and presigma for an existing label.

        Args:
            label_int: Integer label to update.
            values: Tuple of (initial, presigma).
        Raises:
            KeyError: If the label is not found.
        """
        param = self[label_int]
        param.initial, param.presigma = values

    # ---------------------------- Methods ---------------------------- #

    def fix(self, rule: FixRule) -> None:
        """
        Set presigma = -1.0 (fix) for all parameters matching the given rule.

        Args:
            rule: FixRule specifying parameters to fix.
        """
        for param in self._parameters:
            if param.label in rule:
                param.presigma = -1.0

    def write(self) -> None:
        """Write all entries to the target parameters file."""
        self._target.parent.mkdir(parents=True, exist_ok=True)
        with open(self._target, 'w') as f:
            f.write('* Label Initial Presigma\n')
            f.write('Parameter\n\n')
            for param in self._parameters:
                f.write(f'{param}\n')
