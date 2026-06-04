import pytest


@pytest.mark.asyncio
async def test_create_lantern_success(client):
    res = await client.post("/api/v1/lanterns", json={
        "name": "소원 랜턴",
        "image_paths": ["a.jpg", "b.jpg", "c.jpg"],
    })
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "소원 랜턴"
    assert data["status"] == "pending"
    assert "lantern_code" in data


@pytest.mark.asyncio
async def test_create_lantern_with_background_music(client):
    res = await client.post("/api/v1/lanterns", json={
        "name": "음악 랜턴",
        "image_paths": ["a.jpg", "b.jpg", "c.jpg"],
        "background_music": "song.mp3",
    })
    assert res.status_code == 201
    assert res.json()["name"] == "음악 랜턴"


@pytest.mark.asyncio
async def test_create_lantern_missing_name(client):
    res = await client.post("/api/v1/lanterns", json={
        "image_paths": ["a.jpg", "b.jpg", "c.jpg"],
    })
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_create_lantern_wrong_image_count(client):
    res = await client.post("/api/v1/lanterns", json={
        "name": "테스트",
        "image_paths": ["a.jpg", "b.jpg"],
    })
    assert res.status_code == 422
