from dataclasses import dataclass, field


@dataclass(frozen=True)
class FrameState:
    bushes: tuple = field(default_factory=tuple)          # [(cx, cy, area), ...]
    enemies: tuple = field(default_factory=tuple)         # [(cx, cy), ...]
    poison: bool = False
    afk: bool = False
    in_bush: bool = False
    stuck: bool = False
    nearest_bush_dir: tuple | None = None                 # (dx, dy) normalizzato
    dist_to_bush: float = float("inf")
    frame_idx: int = 0
