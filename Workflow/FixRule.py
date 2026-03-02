#!/usr/bin/env python3

from enum import IntEnum
from typing import ClassVar, Union
from Label import Label

class Depth(IntEnum):
    TRACKER = 0
    STATION = 1
    LAYER   = 2
    MODULE  = 3
    SIDE    = 4


class FixRule:
    """Rule for fixing a set of parameters in a millepede step."""

    # ---------------------------- Abbrevation ---------------------------- #

    _labels: ClassVar[dict[str, frozenset[Label]]] = {
        "tracker": frozenset({Label(0)}),
        "IFT":     frozenset({Label(10)}),
        "3ST":     frozenset({Label(20), Label(30), Label(40)}),
    }

    _depths: ClassVar[dict[str, frozenset[Depth]]] = {
        "all":   frozenset(Depth),
        "layer": frozenset({Depth.LAYER}),
        "side":  frozenset({Depth.SIDE}),
    }

    # ---------------------------- Constructor ---------------------------- #
    
    def __init__(self, *names: Union[str, int]):
        """Parse rule from str and int."""
        self._rules: dict[Label, frozenset[Depth]] = {}
        self._name = names

        for name in names:
            if isinstance(name, int):
                label = Label(name)
                if label.is_component:
                    labels = frozenset({label})
                    depths = self._depths["all"]
                else:
                    raise ValueError(
                        f"Invalid FixRule number, "
                        f"must be a component label, got {name}.")

            elif isinstance(name, str):
                if '_' in name:
                    parts = name.split('_')
                    if len(parts) != 2:
                        raise ValueError(
                            f"Invalid FixRule format: {name!r}, "
                            f"must contain exactly one '_'."
                        )
                    elif parts[0] not in self._labels:
                        raise ValueError(
                            f"Unknown label: {parts[0]!r} in {name!r}. "
                            f"Known labels: {list(self._labels)}"
                        )
                    elif parts[1] not in self._depths:
                        raise ValueError(
                            f"Unknown depth: {parts[1]!r} in {name!r}. "
                            f"Known depths: {list(self._depths)}"
                        )
                    labels = self._labels[parts[0]]
                    depths = self._depths[parts[1]]
                elif name in self._labels:
                    labels = self._labels[name]
                    depths = self._depths["all"]
                elif name in self._depths:
                    labels = self._labels["tracker"]
                    depths = self._depths[name]
                else:
                    raise ValueError(
                        f"Unknown FixRule: {name!r}. "
                        f"Must be a label, depth, or '<label>_<depth>'.\n"
                        f"\tLabels: {list(self._labels)}\n"
                        f"\tDepths: {list(self._depths)}"
                    )
            else:
                raise TypeError(f"Invalid name type: {type(name).__name__}")

            for label in labels:
                if label in self._rules:
                    self._rules[label] = self._rules[label] | depths
                else:
                    self._rules[label] = depths

    # -------------------------- Helper Methods -------------------------- #
    
    @property
    def rules(self) -> dict[Label, frozenset[Depth]]:
        return self._rules

    def __repr__(self) -> str:
        return f'FixRule{self._name!r}'

    def __add__(self, other: 'FixRule') -> 'FixRule':
        """Merge two rules by combining their names."""
        return FixRule(*(self._name + other._name))

    def __contains__(self, label: Label) -> bool:
        """Check if a parameter label is covered by this rule."""
        for comp, depths in self._rules.items():
            if label in comp and label.depth in depths:
                return True
        return False