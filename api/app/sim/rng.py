"""Deterministic RNG helpers for the simulation."""
from __future__ import annotations

import random


def make_rng(seed: int) -> random.Random:
    """Create a seeded random.Random (deterministic given the seed)."""
    return random.Random(seed)


def choice(rng: random.Random, seq):
    return rng.choice(list(seq))


def weighted(rng: random.Random, pairs: list[tuple[object, float]]):
    """Weighted choice from [(item, weight), ...]."""
    items = [p[0] for p in pairs]
    weights = [p[1] for p in pairs]
    return rng.choices(items, weights=weights, k=1)[0]
