#!/usr/bin/env python3
from typing import Union

from Label import Label
from FixRule import FixRule



class PedeStep():
    """One pede step in alignment workflow. Only layer by layer at present."""

    def __init__(self, fix: list[Union[str, int, Label]]):
        self._fix: list[FixRule] = []
        for item in fix:
            if isinstance(item, str):
                self._fix.append(FixRule(item))
            elif isinstance(item, Label):
                self._fix.append(FixRule(int(item)))
            elif isinstance(item, int):
                self._fix.append(FixRule(item))
            else:
                raise TypeError(f"Unparseable fix item: {type(item).__name__}")