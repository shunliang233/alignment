#!/usr/bin/env python3
"""Abstract base class for all millepede pipeline steps."""

from abc import ABC, abstractmethod

class Alg(ABC):
    """
    Abstract base for a single step in the millepede pipeline.

    Each concrete subclass encapsulates one external tool invocation and
    binds all environment parameters (directories, executables, paths) at
    construction time, so that ``run()`` only receives the step's data input.

    Subclasses
    ----------
    BinAlg   : kfalign output → mp2input.bin   (wraps 1convert)
    PedeAlg  : ParamIO        → ParamIO         (wraps pede)
    MergeAlg : millepede.res  → inputforalign   (wraps 5.1PedetoDB_ss + 5.2add_param)
    """

    @abstractmethod
    def run(self, *args, **kwargs):
        """Execute this algorithm step and return the result."""
        ...
