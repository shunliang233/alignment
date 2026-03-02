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
from PedeStep import FixRule


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


class ParamReader:
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
            raise FileNotFoundError(f"Source mp2par file not found: {source}")
        self._source = source
        self._target = target
        self._entries: list[Parameter] = self._parse(source)

    def _parse(self, source: Path) -> list[Parameter]:
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
    # TODO: 这些是 Claude 写的，不确定有没有用

    @property
    def entries(self) -> list[Parameter]:
        """All parsed entries in file order."""
        return self._entries

    def __len__(self) -> int:
        return len(self._entries)

    def __iter__(self):
        return iter(self._entries)

    def __getitem__(self, label_int: int) -> Parameter:
        """
        Look up an entry by integer label.

        Raises:
            KeyError: If the label is not found.
        """
        for entry in self._entries:
            if entry.label == label_int:
                return entry
        raise KeyError(f"Label {label_int} not found in {self._source}")

    def __contains__(self, label_int: int) -> bool:
        return any(e.label == label_int for e in self._entries)

    def __setitem__(self, label_int: int, values: tuple[float, float]) -> None:
        """
        Modify initial and/or presigma for a given label.

        Args:
            label_int: Integer label to update.
            values: Tuple of (initial, presigma).
        Raises:
            KeyError: If the label is not found.
        """
        entry = self[label_int]
        entry.initial, entry.presigma = values

    # ---------------------------- Methods ---------------------------- #

    def fix(self, rule: FixRule) -> None:
        """
        Set presigma = -1 (fix) for all entries matching the given rule.

        Args:
            rule: FixRule specifying per-component depths to fix.
        """
        for entry in self._entries:
            for comp, depths in rule.rules.items():
                if entry.label.depth in depths and entry.label in comp:
                    entry.presigma = -1.0
                    break

    def write(self) -> None:
        """
        Write all entries to the target parameters file.
        """
        self._target.parent.mkdir(parents=True, exist_ok=True)
        with open(self._target, 'w') as f:
            f.write('* Label Initial Presigma\n')
            f.write('Parameter\n\n')
            for entry in self._entries:
                f.write(f'{entry}\n')
