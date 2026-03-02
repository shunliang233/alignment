#!/usr/bin/env python3
"""
Label parser for FASER detector alignment parameters.

This module provides a Label class that decodes integer labels into
their hierarchical detector structure components (station, layer, module, etc).
"""

class Label:
    """
    Parser for FASER alignment parameter labels.

    The lowest digit is always the parameter digit:
      0 = the component itself (not an alignment parameter)
      1-6 = alignment parameters

    Example structure (high to low for a 5 digit number):
    - Digit 0: Station (1-4, represent station 0-3)
    - Digit 1: Layer (0-2)
    - Digit 2: Module (0-7)
    - Digit 3: Side (0-1)
    - Digit 4: Param (0-6)
    """

    # ---------------------------- Constructor ---------------------------- #

    def __init__(self, label: int):
        """
        Initialize label parser.

        Args:
            label: Positive integer label (0-99999)
        Raises:
            ValueError: If label is out of valid range
        """
        if label < 0 or label > 99999:
            raise ValueError(f"Invalid Label: {label}, must within [0, 99999]")

        self._label = label
        self._label_str = str(label)
        self._len = len(self._label_str)

        # NOTE: Fail Fast, Validate digit range format immediately
        s = self._label_str
        if not (0 <= int(s[-1]) <= 6):
            raise ValueError(f"Invalid Label: {label}, param digit must be [0, 6].")
        if self._len >= 2 and not (1 <= int(s[0]) <= 4):
            raise ValueError(f"Invalid Label: {label}, station digit must be [1, 4].")
        if self._len >= 3 and not (0 <= int(s[1]) <= 2):
            raise ValueError(f"Invalid Label: {label}, layer digit must be [0, 2].")
        if self._len >= 4 and not (0 <= int(s[2]) <= 7):
            raise ValueError(f"Invalid Label: {label}, module digit must be [0, 7].")
        if self._len >= 5 and not (0 <= int(s[3]) <= 1):
            raise ValueError(f"Invalid Label: {label}, side digit must be [0, 1].")

    # ---------------------------- Properties ---------------------------- #

    @property
    def parameter(self) -> int:
        """Get parameter index [0-6]. 0 means the component itself."""
        return int(self._label_str[-1])

    @property
    def station(self) -> int:
        """Get station index [1-4]."""
        if self._len < 2:
            raise ValueError(f"Label {self._label} doesn't have station info.")
        return int(self._label_str[0])

    @property
    def layer(self) -> int:
        """Get layer index [0-2]."""
        if self._len < 3:
            raise ValueError(f"Label {self._label} doesn't have layer info.")
        return int(self._label_str[1])

    @property
    def module(self) -> int:
        """Get module index [0-7]."""
        if self._len < 4:
            raise ValueError(f"Label {self._label} doesn't have module info.")
        return int(self._label_str[2])

    @property
    def side(self) -> int:
        """Get side index [0-1]."""
        if self._len < 5:
            raise ValueError(f"Label {self._label} doesn't have side info.")
        return int(self._label_str[3])

    @property
    def is_component(self) -> bool:
        """Check if this label represents the component itself (param=0)."""
        return self.parameter == 0

    @property
    def is_parameter(self) -> bool:
        """Check if this label represents a parameter (param=1-6)."""
        return 1 <= self.parameter <= 6

    @property
    def depth(self) -> int:
        """Label depth level (0-4)"""
        return self._len - 1

    # ---------------------------- Magic Methods ---------------------------- #

    def __int__(self) -> int:
        return self._label

    def __str__(self) -> str:
        return self._label_str

    def __repr__(self) -> str:
        return f"Label({self._label})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Label):
            return self._label == other._label
        if isinstance(other, int):
            return self._label == other
        return NotImplemented

    def __hash__(self) -> int:
        # NOTE: Objects which compare equal should have the same hash value.
        # Must entrust hash to int when __eq__ supports int comparison.
        return hash(self._label)

    def __contains__(self, other: 'Label') -> bool:
        """
        Check if a parameter label belongs to this component label.

        Usage: a in b, use b.__contains__(a)

        Rules:
          - self  must be a component label (param=0)
          - other's structural digits must start with self's structural digits
          - e.g. 211 in 210 == True, 21112 in 210 == True, 31112 in 210 == False
        """
        # NOTE: __contains__ should return False instead of raising error.
        if not self.is_component:
            return False
        return other._label_str[:-1].startswith(self._label_str[:-1])
    

