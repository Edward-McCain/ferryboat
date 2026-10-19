from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, Response, status

from app.models import Crossing
from app.schemas import CrossingCreate, CrossingOut, CrossingUpdate, ErrorResponse, StatusChange
from app.store import Store

router = APIRouter(prefix="/api/crossings", tags=["рейсы"])


ERRORS: dict[int | str, dict[str, Any]] = {
    404: {"model": ErrorResponse},
    409: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
}


def get_store(request: Request) -> Store:
    store: object = request.app.state.store
    if not isinstance(store, Store):
        raise RuntimeError("Хранилище не подключено к приложению.")
    return store


StoreDep = Annotated[Store, Depends(get_store)]


def present(crossing: Crossing) -> CrossingOut:
    return CrossingOut.model_validate(crossing)


@router.get("", response_model=list[CrossingOut])
def list_crossings(store: StoreDep) -> list[CrossingOut]:
    return [present(item) for item in store.list_crossings()]


@router.post("", status_code=status.HTTP_201_CREATED, response_model=CrossingOut, responses=ERRORS)
def create_crossing(payload: CrossingCreate, store: StoreDep) -> CrossingOut:
    crossing = store.create(
        departure=payload.departure,
        berth=payload.berth,
        direction=payload.direction,
        note=payload.note,
        capacity=payload.capacity,
    )
    return present(crossing)


@router.get("/{crossing_id}", response_model=CrossingOut, responses=ERRORS)
def read_crossing(crossing_id: str, store: StoreDep) -> CrossingOut:
    return present(store.get(crossing_id))


@router.patch("/{crossing_id}", response_model=CrossingOut, responses=ERRORS)
def update_crossing(crossing_id: str, payload: CrossingUpdate, store: StoreDep) -> CrossingOut:
    crossing = store.update(
        crossing_id,
        fields=set(payload.model_fields_set),
        departure=payload.departure,
        berth=payload.berth,
        direction=payload.direction,
        note=payload.note,
        capacity=payload.capacity,
    )
    return present(crossing)


@router.post("/{crossing_id}/status", response_model=CrossingOut, responses=ERRORS)
def change_status(crossing_id: str, payload: StatusChange, store: StoreDep) -> CrossingOut:
    return present(store.change_status(crossing_id, payload.status))


@router.delete("/{crossing_id}", status_code=status.HTTP_204_NO_CONTENT, responses=ERRORS)
def delete_crossing(crossing_id: str, store: StoreDep) -> Response:
    store.delete(crossing_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
