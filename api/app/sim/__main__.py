"""Simulation CLI.

Usage (inside the api container):
    python -m app.sim history [--days 720]
    python -m app.sim day
    python -m app.sim reset

- `history` initialises the sim and generates N days of history.
- `day` advances the simulation by one day (append-only).
- `reset` drops simulation + operational data so history can be regenerated.
"""
from __future__ import annotations

import argparse

from ..config import settings
from ..db import SessionLocal, engine
from ..models import Base
from .simulator import HISTORY_DAYS, Simulator


def _session():
    return SessionLocal()


def cmd_history(days: int) -> None:
    session = _session()
    try:
        sim = Simulator(session, settings.seed)
        sim.generate_history(days)
        print(f"History generated: {days} days, seed={settings.seed}")
    finally:
        session.close()


def cmd_day() -> None:
    session = _session()
    try:
        sim = Simulator(session, settings.seed)
        sim.advance_day()
        print(f"Advanced to day {sim.day_index}, date={sim.sim_date}")
    finally:
        session.close()


def cmd_reset() -> None:
    # Drop and recreate the operational schema (deterministic regen from scratch).
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Operational schema reset (all sim + source data dropped).")


def main() -> None:
    parser = argparse.ArgumentParser(prog="sim")
    sub = parser.add_subparsers(dest="command", required=True)

    p_hist = sub.add_parser("history")
    p_hist.add_argument("--days", type=int, default=HISTORY_DAYS)

    sub.add_parser("day")
    sub.add_parser("reset")

    args = parser.parse_args()
    if args.command == "history":
        cmd_history(args.days)
    elif args.command == "day":
        cmd_day()
    elif args.command == "reset":
        cmd_reset()


if __name__ == "__main__":
    main()
