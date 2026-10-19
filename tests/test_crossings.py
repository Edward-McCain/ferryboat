import httpx
import pytest

pytestmark = pytest.mark.anyio


def payload(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "departure": "21:40",
        "berth": 2,
        "direction": "island_to_city",
        "capacity": 40,
    }
    data.update(overrides)
    return data


async def create(client: httpx.AsyncClient, **overrides: object) -> dict[str, object]:
    response = await client.post("/api/crossings", json=payload(**overrides))
    assert response.status_code == 201
    body = response.json()
    assert isinstance(body, dict)
    return body


async def test_create_strips_note_and_lists_in_order(client: httpx.AsyncClient) -> None:
    later = await create(client, departure="22:15", berth=1, note="  после полуночи не пойдём  ")
    earlier = await create(client, departure="21:10", berth=1, direction="city_to_island")

    assert later["note"] == "после полуночи не пойдём"
    assert later["status"] == "scheduled"
    assert later["departure"] == "22:15"

    listed = await client.get("/api/crossings")
    assert listed.status_code == 200
    ids = [item["id"] for item in listed.json()]
    assert ids == [earlier["id"], later["id"]]


async def test_validation_names_the_field(client: httpx.AsyncClient) -> None:
    missing_time = await client.post(
        "/api/crossings",
        json={"berth": 2, "direction": "city_to_island", "capacity": 40},
    )
    assert missing_time.status_code == 422
    assert missing_time.json()["error"]["message"] == "Время отхода запишите как 21:40."

    bad_berth = await client.post("/api/crossings", json=payload(berth=9))
    assert bad_berth.status_code == 422
    assert bad_berth.json()["error"]["code"] == "validation"
    assert bad_berth.json()["error"]["message"] == "Причал — число от 1 до 4."


async def test_one_departure_per_berth(client: httpx.AsyncClient) -> None:
    await create(client, direction="city_to_island")
    conflict = await client.post("/api/crossings", json=payload(direction="island_to_city"))
    assert conflict.status_code == 409
    assert conflict.json()["error"]["message"] == "Причал 2 на 21:40 уже занят."


async def test_cancelled_slot_can_be_taken_again(client: httpx.AsyncClient) -> None:
    first = await create(client)
    cancelled = await client.post(
        f"/api/crossings/{first['id']}/status",
        json={"status": "cancelled"},
    )
    assert cancelled.status_code == 200
    second = await create(client)
    assert second["id"] != first["id"]


async def test_status_flow_allows_only_one_boarding(client: httpx.AsyncClient) -> None:
    first = await create(client, departure="21:10", berth=1)
    second = await create(client, departure="21:40", berth=2)

    boarded = await client.post(
        f"/api/crossings/{first['id']}/status",
        json={"status": "boarding"},
    )
    assert boarded.status_code == 200
    assert boarded.json()["status"] == "boarding"

    blocked = await client.post(
        f"/api/crossings/{second['id']}/status",
        json={"status": "boarding"},
    )
    assert blocked.status_code == 409
    assert "посадку" in blocked.json()["error"]["message"]

    departed = await client.post(
        f"/api/crossings/{first['id']}/status",
        json={"status": "departed"},
    )
    assert departed.status_code == 200

    opened = await client.post(
        f"/api/crossings/{second['id']}/status",
        json={"status": "boarding"},
    )
    assert opened.status_code == 200


async def test_cannot_skip_ahead(client: httpx.AsyncClient) -> None:
    crossing = await create(client)
    response = await client.post(
        f"/api/crossings/{crossing['id']}/status",
        json={"status": "departed"},
    )
    assert response.status_code == 409
    assert response.json()["error"]["message"] == "Рейс сейчас в расписании. Так статус не меняют."


async def test_patch_keeps_omitted_fields_and_stops_after_boarding(
    client: httpx.AsyncClient,
) -> None:
    crossing = await create(client, note="у трапа лужа")
    patched = await client.patch(
        f"/api/crossings/{crossing['id']}",
        json={"capacity": 12},
    )
    assert patched.status_code == 200
    assert patched.json()["capacity"] == 12
    assert patched.json()["note"] == "у трапа лужа"

    cleared = await client.patch(f"/api/crossings/{crossing['id']}", json={"note": None})
    assert cleared.json()["note"] is None

    await client.post(f"/api/crossings/{crossing['id']}/status", json={"status": "boarding"})
    locked = await client.patch(f"/api/crossings/{crossing['id']}", json={"berth": 3})
    assert locked.status_code == 409
    assert "расписании" in locked.json()["error"]["message"]


async def test_delete_rules(client: httpx.AsyncClient) -> None:
    scheduled = await create(client, departure="21:10", berth=1)
    removed = await client.delete(f"/api/crossings/{scheduled['id']}")
    assert removed.status_code == 204
    assert removed.content == b""

    boarding = await create(client, departure="21:40", berth=2)
    await client.post(f"/api/crossings/{boarding['id']}/status", json={"status": "boarding"})
    denied = await client.delete(f"/api/crossings/{boarding['id']}")
    assert denied.status_code == 409

    await client.post(f"/api/crossings/{boarding['id']}/status", json={"status": "departed"})
    stayed = await client.delete(f"/api/crossings/{boarding['id']}")
    assert stayed.status_code == 409

    cancelled = await create(client, departure="22:15", berth=1)
    await client.post(f"/api/crossings/{cancelled['id']}/status", json={"status": "cancelled"})
    assert (await client.delete(f"/api/crossings/{cancelled['id']}")).status_code == 204


async def test_missing_crossing(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/crossings/no-such-id")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


async def test_seed_is_chronological(seeded_client: httpx.AsyncClient) -> None:
    body = (await seeded_client.get("/api/crossings")).json()
    assert [item["departure"] for item in body] == ["21:10", "21:40", "22:15", "22:50", "23:20"]
    assert body[1]["status"] == "boarding"
    assert body[-1]["status"] == "cancelled"


async def test_openapi_lists_the_resource(client: httpx.AsyncClient) -> None:
    spec = await client.get("/openapi.json")
    assert spec.status_code == 200
    body = spec.json()
    assert body["info"]["title"] == "Рейс"
    assert "/api/crossings" in body["paths"]
    assert "/api/crossings/{crossing_id}/status" in body["paths"]
