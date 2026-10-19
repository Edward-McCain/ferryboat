from dataclasses import dataclass
from datetime import time
from enum import StrEnum


class Direction(StrEnum):
    CITY_TO_ISLAND = "city_to_island"
    ISLAND_TO_CITY = "island_to_city"


class Status(StrEnum):
    SCHEDULED = "scheduled"
    BOARDING = "boarding"
    DEPARTED = "departed"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class Crossing:
    id: str
    departure: time
    berth: int
    direction: Direction
    status: Status
    note: str | None
    capacity: int
