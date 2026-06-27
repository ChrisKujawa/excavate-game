import json
import os
import constants as C

HIGHSCORE_FILE = os.path.join(os.path.dirname(__file__), "highscores.json")
MAX_ENTRIES = 5


def load() -> list[dict]:
    """Gibt Liste von {'name': str, 'points': int} zurück."""
    if not os.path.exists(HIGHSCORE_FILE):
        return []
    try:
        with open(HIGHSCORE_FILE, "r") as f:
            data = json.load(f)
        # Validierung
        if isinstance(data, list):
            return data[:MAX_ENTRIES]
    except (json.JSONDecodeError, OSError):
        pass
    return []


def save(name: str, points: int) -> list[dict]:
    """Fügt neuen Eintrag ein, sortiert, kürzt auf MAX_ENTRIES und speichert."""
    scores = load()
    scores.append({"name": name[:12], "points": points})
    scores.sort(key=lambda e: e["points"], reverse=True)
    scores = scores[:MAX_ENTRIES]
    try:
        with open(HIGHSCORE_FILE, "w") as f:
            json.dump(scores, f, indent=2)
    except OSError:
        pass
    return scores


def is_highscore(points: int) -> bool:
    """Gibt True zurück wenn der Score in die Top-5 käme."""
    scores = load()
    if len(scores) < MAX_ENTRIES:
        return True
    return points > scores[-1]["points"]
