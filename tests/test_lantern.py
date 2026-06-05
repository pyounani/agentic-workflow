import io

import pytest


def make_images(n=3):
    return [("images", (f"{i}.jpg", io.BytesIO(b"fake"), "image/jpeg")) for i in range(n)]


@pytest.mark.asyncio
async def test_create_lantern_success(client, tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.lantern.UPLOAD_DIR", tmp_path)
    res = await client.post(
        "/api/v1/lanterns",
        files=make_images(3),
        data={"name": "소원 랜턴"},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "소원 랜턴"
    assert data["status"] == "pending"
    assert "lantern_code" in data


@pytest.mark.asyncio
async def test_create_lantern_missing_name(client):
    res = await client.post(
        "/api/v1/lanterns",
        files=make_images(3),
        data={},
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_create_lantern_empty_name(client):
    res = await client.post(
        "/api/v1/lanterns",
        files=make_images(3),
        data={"name": ""},
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_create_lantern_wrong_image_count(client):
    res = await client.post(
        "/api/v1/lanterns",
        files=make_images(2),
        data={"name": "테스트"},
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_create_lantern_too_many_images(client):
    res = await client.post(
        "/api/v1/lanterns",
        files=make_images(4),
        data={"name": "테스트"},
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_create_lantern_no_images(client):
    res = await client.post(
        "/api/v1/lanterns",
        data={"name": "테스트"},
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_create_lantern_non_image_file(client):
    files = [
        ("images", ("doc.txt", io.BytesIO(b"text"), "text/plain")),
        ("images", ("b.jpg",   io.BytesIO(b"fake"), "image/jpeg")),
        ("images", ("c.jpg",   io.BytesIO(b"fake"), "image/jpeg")),
    ]
    res = await client.post(
        "/api/v1/lanterns",
        files=files,
        data={"name": "테스트"},
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_get_lantern_success(client, tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.lantern.UPLOAD_DIR", tmp_path)
    monkeypatch.setattr("app.routers.lantern.process_mood_analysis", lambda code: None)
    create_res = await client.post(
        "/api/v1/lanterns",
        files=make_images(3),
        data={"name": "조회 랜턴"},
    )
    assert create_res.status_code == 201
    lantern_code = create_res.json()["lantern_code"]

    res = await client.get(f"/api/v1/lanterns/{lantern_code}")
    assert res.status_code == 200
    data = res.json()
    assert data["lantern_code"] == lantern_code
    assert data["name"] == "조회 랜턴"
    assert data["status"] == "pending"
    assert len(data["image_paths"]) == 3


@pytest.mark.asyncio
async def test_get_lantern_not_found(client):
    res = await client.get("/api/v1/lanterns/non-existent-code")
    assert res.status_code == 404
    assert res.json()["detail"] == "Lantern 'non-existent-code' not found"
