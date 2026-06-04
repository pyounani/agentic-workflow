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
async def test_create_lantern_wrong_image_count(client, tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.lantern.UPLOAD_DIR", tmp_path)
    res = await client.post(
        "/api/v1/lanterns",
        files=make_images(2),
        data={"name": "테스트"},
    )
    assert res.status_code == 422
