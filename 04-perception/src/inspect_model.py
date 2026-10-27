"""VisionPilot modellerini çalıştırma ve inceleme.

Bağımlılıklar ve model ağırlıkları vision_pilot reposunun README'sine göre kurulur.
Bu dosya vision_pilot'un kendi inference kodunu sarmalar; mantığı kopyalamak yerine
mümkün olduğunca onların fonksiyonlarını import et ve nereden aldığını yorumda belirt.
"""
from __future__ import annotations

import numpy as np


def load_model(name: str):
    """name ∈ {"egolanes", "autosteer"}"""
    raise NotImplementedError


def preprocess(frame: np.ndarray):
    raise NotImplementedError


def infer(model, inputs):
    raise NotImplementedError


def postprocess(name: str, raw):
    raise NotImplementedError


def overlay(frame: np.ndarray, result) -> np.ndarray:
    raise NotImplementedError


if __name__ == "__main__":
    # Örnek: python src/inspect_model.py --video path/to/video.mp4 --model egolanes
    raise SystemExit("Henüz uygulanmadı")
