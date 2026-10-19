from dataclasses import replace
from datetime import time
from threading import Lock
from typing import Self
from uuid import uuid4

from app.errors import Conflict, NotFound
from app.models import Crossing, Direction, Status

# С расписания — посадка или отмена. С посадки — отход или отмена.
# Ушедший и отменённый рейс дальше не двигаются.
ALLOWED: dict[Status, frozenset[Status]] = {
    Status.SCHEDULED: frozenset({Status.BOARDING, Status.CANCELLED}),
    Status.BOARDING: frozenset({Status.DEPARTED, Status.CANCELLED}),
    Status.DEPARTED: frozenset(),
    Status.CANCELLED: frozenset(),
}


def _pick[T](fields: set[str], name: str, value: T | None, current: T) -> T:
    if name in fields and value is not None:
        return value
    return current


STATUS_LABEL = {
    Status.SCHEDULED: "в расписании",
    Status.BOARDING: "на посадке",
    Status.DEPARTED: "ушёл",
    Status.CANCELLED: "отменён",
}


def _seed() -> tuple[Crossing, ...]:
    return (
        Crossing(
            id="seed-2110",
            departure=time(21, 10),
            berth=1,
            direction=Direction.CITY_TO_ISLAND,
            status=Status.SCHEDULED,
            note="Автобус с вокзала опаздывает на десять минут.",
            capacity=40,
        ),
        Crossing(
            id="seed-2140",
            departure=time(21, 40),
            berth=2,
            direction=Direction.ISLAND_TO_CITY,
            status=Status.BOARDING,
            note=None,
            capacity=36,
        ),
        Crossing(
            id="seed-2215",
            departure=time(22, 15),
            berth=1,
            direction=Direction.CITY_TO_ISLAND,
            status=Status.SCHEDULED,
            note=None,
            capacity=40,
        ),
        Crossing(
            id="seed-2250",
            departure=time(22, 50),
            berth=2,
            direction=Direction.ISLAND_TO_CITY,
            status=Status.SCHEDULED,
            note=None,
            capacity=28,
        ),
        Crossing(
            id="seed-2320",
            departure=time(23, 20),
            berth=3,
            direction=Direction.CITY_TO_ISLAND,
            status=Status.CANCELLED,
            note="Отменил: волна выше трапа.",
            capacity=40,
        ),
    )


class Store:
    def __init__(self) -> None:
        self._items: dict[str, Crossing] = {}
        # Sync-ручки выполняются в пуле потоков, лист у них общий.
        self._lock: Lock = Lock()

    @classmethod
    def with_seed(cls) -> Self:
        store = cls()
        for crossing in _seed():
            store._items[crossing.id] = crossing
        return store

    def list_crossings(self) -> list[Crossing]:
        with self._lock:
            return sorted(
                self._items.values(),
                key=lambda item: (item.departure, item.berth, item.id),
            )

    def get(self, crossing_id: str) -> Crossing:
        with self._lock:
            return self._must(crossing_id)

    def create(
        self,
        *,
        departure: time,
        berth: int,
        direction: Direction,
        note: str | None,
        capacity: int,
    ) -> Crossing:
        with self._lock:
            self._ensure_slot(departure, berth, ignore_id=None)
            crossing = Crossing(
                id=uuid4().hex[:12],
                departure=departure,
                berth=berth,
                direction=direction,
                status=Status.SCHEDULED,
                note=note,
                capacity=capacity,
            )
            self._items[crossing.id] = crossing
            return crossing

    def update(
        self,
        crossing_id: str,
        *,
        fields: set[str],
        departure: time | None,
        berth: int | None,
        direction: Direction | None,
        note: str | None,
        capacity: int | None,
    ) -> Crossing:
        with self._lock:
            current = self._must(crossing_id)
            # Причал и время уже нельзя двигать: на посадке люди стоят у конкретного трапа.
            if current.status is not Status.SCHEDULED:
                raise Conflict("Поправки принимаю, только пока рейс в расписании.")
            updated = replace(
                current,
                departure=_pick(fields, "departure", departure, current.departure),
                berth=_pick(fields, "berth", berth, current.berth),
                direction=_pick(fields, "direction", direction, current.direction),
                note=note if "note" in fields else current.note,
                capacity=_pick(fields, "capacity", capacity, current.capacity),
            )
            self._ensure_slot(updated.departure, updated.berth, ignore_id=current.id)
            self._items[current.id] = updated
            return updated

    def change_status(self, crossing_id: str, status: Status) -> Crossing:
        with self._lock:
            current = self._must(crossing_id)
            if status not in ALLOWED[current.status]:
                label = STATUS_LABEL[current.status]
                raise Conflict(f"Рейс сейчас {label}. Так статус не меняют.")
            if status is Status.BOARDING and self._other_boarding(current.id):
                raise Conflict("Сначала закройте посадку на другом рейсе.")
            updated = replace(current, status=status)
            self._items[current.id] = updated
            return updated

    def delete(self, crossing_id: str) -> None:
        with self._lock:
            current = self._must(crossing_id)
            if current.status is Status.BOARDING:
                raise Conflict(
                    "Рейс на посадке не убираю с листа. Его можно отменить или отметить отход."
                )
            if current.status is Status.DEPARTED:
                raise Conflict("Ушедший рейс остаётся в листе до конца смены.")
            del self._items[current.id]

    def _must(self, crossing_id: str) -> Crossing:
        crossing = self._items.get(crossing_id)
        if crossing is None:
            raise NotFound("Рейса с таким номером нет.")
        return crossing

    def _ensure_slot(self, departure: time, berth: int, ignore_id: str | None) -> None:
        # Один причал — один отход в минуту. Отменённый слот свободен.
        for item in self._items.values():
            if item.id == ignore_id or item.status is Status.CANCELLED:
                continue
            if item.departure == departure and item.berth == berth:
                clock = departure.strftime("%H:%M")
                raise Conflict(f"Причал {berth} на {clock} уже занят.")

    def _other_boarding(self, crossing_id: str) -> bool:
        return any(
            item.status is Status.BOARDING and item.id != crossing_id
            for item in self._items.values()
        )
