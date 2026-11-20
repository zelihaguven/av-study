"""Grafik etiketleri için iki dil. Varsayılan Türkçe; AV_LANG=en ile İngilizce.

    AV_LANG=en python 02-control/src/plots.py   → İngilizce grafikler results/en/ altına
Türkçe grafikler ve varsayılan davranış değişmez.
"""
from __future__ import annotations

import os
from pathlib import Path

LANG = os.environ.get("AV_LANG", "tr").lower()
EN = LANG == "en"


def L(tr: str, en: str) -> str:
    """Seçili dile göre etiket."""
    return en if EN else tr


def num(x: float, fmt: str = "{:.1f}") -> str:
    """Sayı biçimi: Türkçede ondalık virgül, İngilizcede nokta."""
    s = fmt.format(x)
    return s if EN else s.replace(".", ",")


def results_dir(base: Path) -> Path:
    """İngilizcede results/en/, Türkçede results/."""
    d = base / "en" if EN else base
    d.mkdir(parents=True, exist_ok=True)
    return d
