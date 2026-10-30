"""Server-owned board generation for bGen.

The zero-freshness path mirrors Kev's normal and stacked generation rules.
Freshness controls the penalty applied to recently used squares, while stale
duration controls how many generations that penalty takes to recover.
"""

import json
import random
from pathlib import Path

from board_generators.daft import goals


BOARD_SIZE = 25
DEFAULT_FRESHNESS = 100
DEFAULT_STALE_DURATION = 10
DEFAULT_GRAFFITI_DISTRIBUTION = [0.1915, 0.3170, 0.3038, 0.1877]
DISTRICT_BY_PREFIX = {
    "Dog": "shibuya_cho",
    "Shi": "shibuya_cho",
    "Chu": "shibuya_cho",
    "Hik": "shibuya_cho",
    "RDH": "kogane_cho",
    "Sew": "kogane_cho",
    "Btm": "kogane_cho",
    "Kib": "kogane_cho",
    "FRZ": "kogane_cho",
    "99t": "benten_cho",
    "Sta": "benten_cho",
    "SDP": "benten_cho",
    "Sky": "benten_cho",
    "HWY": "benten_cho",
}


def _goal_name(goal):
    return f"{goal[0]} {goal[1].strip()}"


def _catalog():
    graffiti = []
    characters = []
    souls = []
    for goal in goals:
        name = _goal_name(goal)
        if "GRAFFITI" in name:
            graffiti.append(name)
        elif "Unlock" in name:
            characters.append(name)
        else:
            souls.append(name)
    return souls, characters, graffiti


SOULS, CHARACTERS, GRAFFITI = _catalog()


def _district(name):
    return DISTRICT_BY_PREFIX.get(name[:3])


GRAFFITI_BY_DISTRICT = {
    "shibuya_cho": [item for item in GRAFFITI if _district(item) == "shibuya_cho"],
    "kogane_cho": [item for item in GRAFFITI if _district(item) == "kogane_cho"],
    "benten_cho": [item for item in GRAFFITI if _district(item) == "benten_cho"],
}


def _normalise_distribution(values):
    if not isinstance(values, list) or len(values) != 4:
        return DEFAULT_GRAFFITI_DISTRIBUTION[:]
    cleaned = [max(0.0, float(value)) for value in values]
    total = sum(cleaned)
    if total <= 0:
        return DEFAULT_GRAFFITI_DISTRIBUTION[:]
    return [value / total for value in cleaned]


def _freshness_weight(freshness, stale_duration, boards_ago):
    freshness = max(0.0, min(1.0, float(freshness) / 100.0))
    stale_duration = max(1.0, float(stale_duration))
    recovery = min(1.0, max(0.0, float(boards_ago)) / stale_duration)
    return (1.0 - freshness) + (freshness * recovery)


def _weighted_choice(items, rng, freshness, stale_duration, history):
    if not items:
        raise ValueError("Cannot choose from an empty objective pool")

    if float(freshness) <= 0 or not history:
        return items[rng.randrange(len(items))]

    weights = []
    for item in items:
        last_seen = history.get(item)
        if last_seen is None:
            weights.append(1.0)
            continue
        boards_ago = max(0, history["generation"] - last_seen)
        weights.append(_freshness_weight(freshness, stale_duration, boards_ago))

    if not any(weights):
        return items[rng.randrange(len(items))]

    return rng.choices(items, weights=weights, k=1)[0]


def _take_from_pool(pool, count, rng, freshness, stale_duration, history):
    pool = list(pool)
    selected = []
    for _ in range(min(count, len(pool))):
        choice = _weighted_choice(pool, rng, freshness, stale_duration, history)
        selected.append(choice)
        pool.remove(choice)
    return selected


def _choose_graffiti(count, rng, freshness, stale_duration, history):
    selected = []
    pools = {district: list(items) for district, items in GRAFFITI_BY_DISTRICT.items()}
    for _ in range(count):
        available = [pool for pool in pools.values() if pool]
        district_pool = available[rng.randrange(len(available))]
        choice = _weighted_choice(
            district_pool,
            rng,
            freshness,
            stale_duration,
            history,
        )
        selected.append(choice)
        district_pool.remove(choice)
    return selected


def _choose_nongraffiti(count, stacked_district, rng, freshness, stale_duration, history):
    target_count = count
    pools = {
        "shibuya_cho": [item for item in SOULS + CHARACTERS if _district(item) == "shibuya_cho"],
        "kogane_cho": [item for item in SOULS + CHARACTERS if _district(item) == "kogane_cho"],
        "benten_cho": [item for item in SOULS + CHARACTERS if _district(item) == "benten_cho"],
    }
    selected = []

    if stacked_district in pools:
        stacked_count = rng.randint(10, 13)
        stacked_count = min(stacked_count, count)
        selected.extend(
            _take_from_pool(
                pools[stacked_district],
                stacked_count,
                rng,
                freshness,
                stale_duration,
                history,
            )
        )
        count -= stacked_count
        for item in selected:
            pools[stacked_district].remove(item)

    while len(selected) < target_count:
        available = [(district, pool) for district, pool in pools.items() if pool]
        if not available:
            break
        _, pool = available[rng.randrange(len(available))]
        choice = _weighted_choice(pool, rng, freshness, stale_duration, history)
        selected.append(choice)
        pool.remove(choice)

    return selected


def _has_simple_bingos(squares):
    rows = set()
    columns = set()
    main_diagonal = 0
    reverse_diagonal = 0
    for index, square in enumerate(squares):
        if "GRAFFITI" not in square:
            continue
        row, column = divmod(index, 5)
        if row == column:
            main_diagonal += 1
        if row + column == 4:
            reverse_diagonal += 1
        if row in rows or column in columns or main_diagonal > 1 or reverse_diagonal > 1:
            return False
        rows.add(row)
        columns.add(column)
    return True


def _choose_graffiti_count(rng, distribution):
    roll = rng.random()
    cumulative = 0.0
    for count, probability in enumerate(distribution, start=1):
        cumulative += probability
        if roll < cumulative:
            return count
    return 4


class BGen:
    def __init__(self, history_file="bgen_history.json"):
        self.history_file = Path(history_file)
        self.history = {"generation": 0, "last_seen": {}}
        self.load_history()

    def load_history(self):
        if not self.history_file.exists():
            return
        try:
            with self.history_file.open("r") as handle:
                loaded = json.load(handle)
            self.history = {
                "generation": int(loaded.get("generation", 0)),
                "last_seen": dict(loaded.get("last_seen", {})),
            }
        except (OSError, ValueError, TypeError):
            self.history = {"generation": 0, "last_seen": {}}

    def save_history(self):
        with self.history_file.open("w") as handle:
            json.dump(self.history, handle, indent=2, sort_keys=True)

    def record_board(self, board):
        self.history["generation"] += 1
        generation = self.history["generation"]
        for item in board:
            square = item.get("name") if isinstance(item, dict) else item
            if square:
                self.history["last_seen"][square] = generation
        self.save_history()
        return generation

    def generate(
        self,
        stacked_district=None,
        freshness=DEFAULT_FRESHNESS,
        stale_duration=DEFAULT_STALE_DURATION,
        graffiti_distribution=None,
        simple_bingos=True,
        seed=None,
    ):
        rng = random.Random(seed)
        distribution = _normalise_distribution(graffiti_distribution)
        history = dict(self.history["last_seen"])
        history["generation"] = self.history["generation"]

        for _ in range(1000):
            graffiti = _choose_graffiti_count(rng, distribution)
            graffiti_squares = _choose_graffiti(
                graffiti,
                rng,
                freshness,
                stale_duration,
                history,
            )
            nongraffiti_squares = _choose_nongraffiti(
                BOARD_SIZE - graffiti,
                stacked_district,
                rng,
                freshness,
                stale_duration,
                history,
            )
            squares = graffiti_squares + nongraffiti_squares
            rng.shuffle(squares)
            if not simple_bingos or _has_simple_bingos(squares):
                break
        else:
            raise RuntimeError("Unable to satisfy the simple bingo constraint")

        return {
            "board": [{"name": square, "color": "#101010"} for square in squares],
            "seed": seed,
            "generation": self.history["generation"] + 1,
            "graffiti_count": len(graffiti_squares),
            "graffiti_distribution": distribution,
            "freshness": freshness,
            "stale_duration": stale_duration,
        }
