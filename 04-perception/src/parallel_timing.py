"""B7: üç modeli sırayla ve paralel (VisionPilot'taki std::async gibi) çalıştırınca kare süresi.

onnxruntime çalışırken GIL'i bırakır, bu yüzden Python thread'leri gerçek paralellik verir. Her oturumun kendi
iç thread havuzu var (intra_op); paralel çalışırken çekirdekleri paylaşmaları gerekir.

    VISIONPILOT_DIR=... python 04-perception/src/parallel_timing.py
"""
import os
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import onnxruntime as ort

from inspect_model import weights_dir

NAMES = ("autosteer", "autospeed", "autodrive")


def sessions(intra: int):
    out = {}
    for n in NAMES:
        o = ort.SessionOptions()
        o.intra_op_num_threads = intra
        out[n] = ort.InferenceSession(str(weights_dir() / f"{n}_fp32.onnx"), o, providers=["CPUExecutionProvider"])
    return out


def feeds(sess):
    x = np.random.default_rng(0).random((1, 3, 512, 1024), dtype=np.float32)
    return {n: {i.name: x for i in s.get_inputs()} for n, s in sess.items()}


def bench(fn, reps=12):
    for _ in range(3):
        fn()
    ts = []
    for _ in range(reps):
        t = time.perf_counter()
        fn()
        ts.append(time.perf_counter() - t)
    return 1e3 * float(np.median(ts))


def main():
    cores = os.cpu_count()
    print(f"CPU çekirdeği: {cores}")
    for intra in sorted({0, 1, 2, cores}):
        sess = sessions(intra)
        fd = feeds(sess)
        seq = bench(lambda: [sess[n].run(None, fd[n]) for n in NAMES])
        pool = ThreadPoolExecutor(max_workers=3)
        par = bench(lambda: [f.result() for f in [pool.submit(sess[n].run, None, fd[n]) for n in NAMES]])
        pool.shutdown()
        label = "varsayılan" if intra == 0 else str(intra)
        print(f"  intra_op = {label:10s} sıralı {seq:6.0f} ms ({1e3 / seq:4.1f} Hz) | paralel {par:6.0f} ms ({1e3 / par:4.1f} Hz)")


if __name__ == "__main__":
    main()
