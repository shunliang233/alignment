#!/usr/bin/env python3
"""
Pydantic schema for config.json.

Defines the full structure of the configuration file so that every field
is type-checked at load time (model_validate raises ValidationError on
any mismatch or missing key, before the program does any real work).

Usage
-----
    import json
    from pathlib import Path
    from Config import AppConfig

    cfg = AppConfig.model_validate(json.loads(Path("config.json").read_text()))
    print(cfg.raw.year)            # int, validated
    print(cfg.set.steps[0].pede)   # list[FixRule], validated
"""

import re
import string
from typing import Annotated
from pathlib import Path
from pydantic import AfterValidator, BaseModel, model_validator

from RawList import RawList
from Workflow.FixRule import FixRule


def _resolve_interpolations(data: dict) -> dict:
    """
    Expand all ${...} cross-references within a nested dict.

    Two reference styles are supported:
      ${a.b.c}   — relative: start from the same sibling dict, then traverse.
      ${.a.b.c}  — absolute: leading dot, traverse from root.

    Performs repeated passes until stable (handles chained references).
    Runtime placeholders using {name} syntax are left untouched.
    """
    def _traverse(node: dict, path: str) -> str:
        for key in path.split('.'):
            node = node[key]
        return str(node)

    def _expand(obj, root: dict, local: dict) -> object:
        if isinstance(obj, dict):
            return {k: _expand(v, root, obj) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_expand(v, root, local) for v in obj]
        if isinstance(obj, str) and '${' in obj:
            def _replace(m: re.Match) -> str:
                ref = m.group(1)
                if ref.startswith('.'):
                    # Absolute: ${.tpl.dir} → root["tpl"]["dir"]
                    return _traverse(root, ref.lstrip('.'))
                else:
                    # Relative: ${a.b.c} → local["a"]["b"]["c"]
                    first = ref.split('.')[0]
                    if first not in local:
                        raise KeyError(
                            f"Relative reference ${{{ref!r}}} not found in "
                            f"sibling keys {list(local)}. "
                            f"Use ${{.path.to.key}} for absolute reference.")
                    return _traverse(local, ref)
            return re.sub(r'\$\{([^}]+)\}', _replace, obj)
        return obj

    for _ in range(10):
        resolved = _expand(data, data, data)
        assert isinstance(resolved, dict)
        if resolved == data:
            break
        data = resolved
    return data


def fmt(*keys: str) -> AfterValidator:
    """Return an AfterValidator that checks a template string's placeholders.

    Raises ValidationError if the set of named placeholders in the string
    does not exactly match *keys*.
    """
    expected = frozenset(keys)
    def _check(v: str) -> str:
        found = {field for _, field, _, _ in string.Formatter().parse(v)
                 if field is not None}
        if found != expected:
            raise ValueError(f"Wrong placeholders: expected {set(expected)}, "
                             f"found {found}")
        return v
    return AfterValidator(_check)


# ==================== raw ====================

class RawConfig(BaseModel):
    year:    int
    run:     int
    files:   RawList
    initial: Path
    format:  Annotated[str, fmt('year', 'run', 'files')]


# ==================== set ====================

class StepConfig(BaseModel):
    iters:   int
    reco:    int
    comment: str
    pedes:   list[FixRule]

class SetConfig(BaseModel):
    dir:   Annotated[str, fmt('set', 'iters', 'reco', 'comment')]
    iter:  Annotated[str, fmt('iter')]
    reco:  str
    pede:  Annotated[str, fmt('pede')]
    steps: list[StepConfig]


# ==================== data ====================

class DataConfig(BaseModel):
    dir:    Annotated[str, fmt('format')]
    config: str


# ==================== dag ====================

class LogsConfig(BaseModel):
    dir:      Annotated[str, fmt('iter')]
    recoerr:  Annotated[str, fmt('iter', 'file')]
    recolog:  Annotated[str, fmt('iter', 'file')]
    recoout:  Annotated[str, fmt('iter', 'file')]
    milleerr: Annotated[str, fmt('iter')]
    millelog: Annotated[str, fmt('iter')]
    milleout: Annotated[str, fmt('iter')]

class DagIterConfig(BaseModel):
    dir:      Annotated[str, fmt('iter')]
    recojob:  Annotated[str, fmt('iter', 'file')]
    recosub:  Annotated[str, fmt('iter', 'file')]
    millejob: Annotated[str, fmt('iter')]
    millesub: Annotated[str, fmt('iter')]
    logs:     LogsConfig

class DagConfig(BaseModel):
    dir:      Annotated[str, fmt('format')]
    file:     str
    recoexe:  str
    milleexe: str
    iter:     DagIterConfig


# ==================== tpl ====================

class TplConfig(BaseModel):
    dir:      Path
    recosub:  Path
    recoexe:  Path
    millesub: Path
    milleexe: Path


# ==================== src ====================

class SrcConfig(BaseModel):
    dir: Path


# ==================== env ====================

class CalypsoConfig(BaseModel):
    asetup: Path
    setup:  Path

class EnvConfig(BaseModel):
    calypso: CalypsoConfig
    pede:    Path
    root:    Path


# ==================== top-level ====================

class AppConfig(BaseModel):
    raw:  RawConfig
    set:  SetConfig
    data: DataConfig
    dag:  DagConfig
    tpl:  TplConfig
    src:  SrcConfig
    env:  EnvConfig

    @model_validator(mode='before')
    @classmethod
    def _interpolate(cls, data: dict) -> dict:
        """Expand ${a.b.c} cross-references before field validation."""
        return _resolve_interpolations(data)
