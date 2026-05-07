#!/usr/bin/env python3
"""Analisi offline metriche sessioni bot da SQLite.

Uso:
    python scripts/analyze_metrics.py [--db PATH] [--days N] [--variant NOME]

Output: statistiche su placement, cause di morte, A/B comparison, state dwell time.
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

# Default DB path relativo alla root del progetto
_DEFAULT_DB = Path(__file__).parent.parent / "logs" / "brawl_bot.db"


def _connect(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        print(f"[ERROR] DB non trovato: {db_path}", file=sys.stderr)
        sys.exit(1)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def report_global(conn: sqlite3.Connection, days: int) -> None:
    """Performance globale ultimi N giorni."""
    print(f"\n{'='*50}")
    print(f"PERFORMANCE GLOBALE (ultimi {days} giorni)")
    print(f"{'='*50}")

    rows = conn.execute("""
        SELECT
            COUNT(*)                        AS matches,
            ROUND(AVG(placement), 2)        AS avg_placement,
            ROUND(100.0 * SUM(CASE WHEN placement <= 4 THEN 1 ELSE 0 END) / COUNT(*), 1)
                                            AS top4_pct,
            ROUND(100.0 * SUM(CASE WHEN placement = 1 THEN 1 ELSE 0 END) / COUNT(*), 1)
                                            AS win_pct,
            ROUND(AVG(duration_sec), 0)     AS avg_duration_s,
            ROUND(AVG(cubes_collected), 2)  AS avg_cubes
        FROM matches
        WHERE ts_start >= datetime('now', ?)
          AND placement IS NOT NULL
    """, (f"-{days} days",)).fetchone()

    if rows and rows["matches"] > 0:
        print(f"  Partite:        {rows['matches']}")
        print(f"  Avg placement:  {rows['avg_placement']} (target < 5.5)")
        print(f"  Top-4 rate:     {rows['top4_pct']}%")
        print(f"  Win rate:       {rows['win_pct']}%")
        print(f"  Avg durata:     {rows['avg_duration_s']}s")
        print(f"  Avg cubes:      {rows['avg_cubes']}")
    else:
        print("  Nessun dato disponibile.")


def report_death_causes(conn: sqlite3.Connection, days: int) -> None:
    """Top cause di morte."""
    print(f"\n{'='*50}")
    print("CAUSE DI MORTE")
    print(f"{'='*50}")

    rows = conn.execute("""
        SELECT death_cause,
               COUNT(*) AS n,
               ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct,
               ROUND(AVG(duration_sec), 0) AS avg_duration_s
        FROM matches
        WHERE ts_start >= datetime('now', ?)
          AND death_cause IS NOT NULL
          AND death_cause != 'unknown'
        GROUP BY death_cause
        ORDER BY n DESC
    """, (f"-{days} days",)).fetchall()

    for r in rows:
        print(f"  {r['death_cause']:12s}  {r['n']:4d} match  {r['pct']:5.1f}%  avg {r['avg_duration_s']}s")


def report_ab_comparison(conn: sqlite3.Connection, days: int) -> None:
    """Confronto A/B per policy_variant."""
    print(f"\n{'='*50}")
    print("A/B TEST per POLICY VARIANT")
    print(f"{'='*50}")

    rows = conn.execute("""
        SELECT
            policy_variant,
            COUNT(*) AS matches,
            ROUND(AVG(placement), 2) AS avg_placement,
            ROUND(100.0 * SUM(CASE WHEN placement <= 4 THEN 1 ELSE 0 END) / COUNT(*), 1)
                AS top4_pct,
            ROUND(AVG(cubes_collected), 2) AS avg_cubes
        FROM matches
        WHERE ts_start >= datetime('now', ?)
          AND placement IS NOT NULL
        GROUP BY policy_variant
        ORDER BY avg_placement ASC
    """, (f"-{days} days",)).fetchall()

    if not rows:
        print("  Nessun dato per A/B.")
        return

    for r in rows:
        marker = " ← BEST" if r == rows[0] else ""
        print(
            f"  {r['policy_variant']:12s}  n={r['matches']:3d}  "
            f"avg={r['avg_placement']:4.2f}  top4={r['top4_pct']:5.1f}%  "
            f"cubes={r['avg_cubes']:4.2f}{marker}"
        )


def report_state_dwell(conn: sqlite3.Connection, days: int) -> None:
    """Tempo medio passato in ogni stato (da state_transitions)."""
    print(f"\n{'='*50}")
    print("STATE DWELL TIME (transizioni pre-morte)")
    print(f"{'='*50}")

    rows = conn.execute("""
        SELECT t.to_state AS state, COUNT(*) AS transitions
        FROM state_transitions t
        JOIN matches m ON t.match_id = m.match_id
        WHERE m.ts_start >= datetime('now', ?)
          AND m.placement IS NOT NULL
        GROUP BY t.to_state
        ORDER BY transitions DESC
    """, (f"-{days} days",)).fetchall()

    total = sum(r["transitions"] for r in rows) or 1
    for r in rows:
        pct = 100.0 * r["transitions"] / total
        bar = "█" * int(pct / 2)
        print(f"  {r['state']:10s}  {r['transitions']:5d}  {pct:5.1f}%  {bar}")


def report_fleeing_before_death(conn: sqlite3.Connection, days: int) -> None:
    """Bug hunter: transizioni che precedono morte nel giro di 5 secondi."""
    print(f"\n{'='*50}")
    print("TRANSIZIONI PRE-MORTE (ultimi 5s di vita)")
    print(f"{'='*50}")

    rows = conn.execute("""
        SELECT t.from_state || ' → ' || t.to_state AS transition,
               COUNT(*) AS n
        FROM state_transitions t
        JOIN matches m ON t.match_id = m.match_id
        WHERE m.ts_start >= datetime('now', ?)
          AND m.placement IS NOT NULL
          AND m.placement > 7                    -- morti precoci
          AND m.duration_sec IS NOT NULL
          AND (m.duration_sec - t.frame_idx / 20.0) < 5.0
        GROUP BY transition
        ORDER BY n DESC
        LIMIT 10
    """, (f"-{days} days",)).fetchall()

    for r in rows:
        print(f"  {r['transition']:25s}  x{r['n']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analisi metriche brawl-bot")
    parser.add_argument("--db", type=Path, default=_DEFAULT_DB)
    parser.add_argument("--days", type=int, default=7, help="Ultimi N giorni")
    parser.add_argument("--variant", type=str, default=None, help="Filtra policy_variant")
    args = parser.parse_args()

    conn = _connect(args.db)

    report_global(conn, args.days)
    report_death_causes(conn, args.days)
    report_ab_comparison(conn, args.days)
    report_state_dwell(conn, args.days)
    report_fleeing_before_death(conn, args.days)

    conn.close()
    print(f"\n[DB] {args.db}")


if __name__ == "__main__":
    main()
