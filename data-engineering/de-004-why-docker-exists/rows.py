"""The ten rows from DE-01 (file rows 33394-33403), and the connection string."""

ROWS = [
    ("492200", "20879", None, 6, "2009-12-15 16:06:00", 0.00, None),
    ("C492201", "84558A", "3D DOG PICTURE PLAYING CARDS", -25, "2009-12-15 16:15:00", 2.95, 14062),
    ("492202", "21536", "DAIRY MAID  SMALL  MILK JUG", 4, "2009-12-15 16:23:00", 2.10, 15514),
    ("492202", "20989", "URBAN CHIC CHOPSTICKS SET/5", 8, "2009-12-15 16:23:00", 1.95, 15514),
    ("492202", "22301", "COFFEE MUG CAT + BIRD DESIGN", 18, "2009-12-15 16:23:00", 2.55, 15514),
    ("492202", "22302", "COFFEE MUG PEARS  DESIGN", 6, "2009-12-15 16:23:00", 2.55, 15514),
    ("492202", "85107", "CUT GLASS T-LIGHT HOLDER OCTAGON", 12, "2009-12-15 16:23:00", 2.55, 15514),
    ("492202", "21311", "SET/4 BIRD MIRROR MAGNETS", 24, "2009-12-15 16:23:00", 2.10, 15514),
    ("492202", "21307", "SET/4 BUTTERFLY MIRROR MAGNETS", 24, "2009-12-15 16:23:00", 2.10, 15514),
    ("492202", "85107", "CUT GLASS T-LIGHT HOLDER OCTAGON", 12, "2009-12-15 16:23:00", 2.55, 15514),
]


def conninfo(environ) -> str:
    """Build a libpq connection string from DB_PASSWORD (and optional DB_PORT)."""
    password = environ.get("DB_PASSWORD", "")
    if not password or password == "change-me":
        raise RuntimeError("DB_PASSWORD is missing or still says change-me. Edit .env.")
    port = environ.get("DB_PORT", "5432")
    if not port.isdigit():
        raise RuntimeError(f"DB_PORT must be a number, got {port!r}.")
    return f"host=127.0.0.1 port={port} user=postgres dbname=postgres password={password}"
