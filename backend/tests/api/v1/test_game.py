"""
Tests for Game API endpoints.
"""
import pytest
from httpx import AsyncClient


class TestListCategories:
    """Tests for GET /api/v1/games/categories"""

    async def test_list_categories_empty(self, client: AsyncClient):
        """Empty list returns 200 with empty array."""
        response = await client.get("/api/v1/games/categories")

        assert response.status_code == 200
        # May have default categories from fixtures, so just check it's a list
        assert isinstance(response.json(), list)

    async def test_list_categories_with_data(
        self, auth_client: AsyncClient
    ):
        """List returns created categories."""
        # Create a category first
        payload = {
            "name": "Role-Playing Games",
            "slug": "rpg",
        }
        create_resp = await auth_client.post("/api/v1/games/categories", json=payload)
        assert create_resp.status_code == 201

        # List should contain it
        response = await auth_client.get("/api/v1/games/categories")

        assert response.status_code == 200
        data = response.json()
        assert any(c["slug"] == "rpg" for c in data)


class TestCreateCategory:
    """Tests for POST /api/v1/games/categories"""

    async def test_create_category_success(self, auth_client: AsyncClient):
        """Create returns 201 with created entity."""
        payload = {
            "name": "Board Games",
            "slug": "board-games",
            "name_i18n": {"fr": "Jeux de plateau"},
        }

        response = await auth_client.post("/api/v1/games/categories", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Board Games"
        assert data["slug"] == "board-games"
        assert data["name_i18n"]["fr"] == "Jeux de plateau"
        assert "id" in data

    async def test_create_category_unauthorized(self, client: AsyncClient):
        """Create without auth returns 401."""
        payload = {
            "name": "Card Games",
            "slug": "card-games",
        }

        response = await client.post("/api/v1/games/categories", json=payload)
        assert response.status_code == 401

    async def test_create_category_duplicate_slug(self, auth_client: AsyncClient):
        """Duplicate slug returns 400."""
        payload = {
            "name": "Category 1",
            "slug": "same-slug",
        }

        # Create first one
        response1 = await auth_client.post("/api/v1/games/categories", json=payload)
        assert response1.status_code == 201

        # Try to create duplicate
        payload["name"] = "Category 2"
        response2 = await auth_client.post("/api/v1/games/categories", json=payload)

        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"]


class TestGetCategory:
    """Tests for GET /api/v1/games/categories/{id}"""

    async def test_get_category_success(self, auth_client: AsyncClient):
        """Get existing category returns 200."""
        # Create first
        payload = {
            "name": "Get Test Category",
            "slug": "get-test-category",
        }
        create_response = await auth_client.post("/api/v1/games/categories", json=payload)
        category_id = create_response.json()["id"]

        # Get it
        response = await auth_client.get(f"/api/v1/games/categories/{category_id}")

        assert response.status_code == 200
        assert response.json()["name"] == "Get Test Category"

    async def test_get_category_not_found(self, client: AsyncClient):
        """Get non-existent category returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = await client.get(f"/api/v1/games/categories/{fake_id}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Category not found"


class TestListGames:
    """Tests for GET /api/v1/games/"""

    async def test_list_games_empty(self, client: AsyncClient):
        """Empty list returns 200 with empty array."""
        response = await client.get("/api/v1/games/")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_list_games_with_data(self, auth_client: AsyncClient):
        """List returns created games."""
        # Create category first
        category_payload = {
            "name": "Test Category for Games",
            "slug": "test-category-games",
        }
        category_resp = await auth_client.post("/api/v1/games/categories", json=category_payload)
        category_id = category_resp.json()["id"]

        # Create a game
        game_payload = {
            "title": "Test Game",
            "category_id": category_id,
            "min_players": 2,
            "max_players": 6,
        }
        create_resp = await auth_client.post("/api/v1/games/", json=game_payload)
        assert create_resp.status_code == 201

        # List should contain it
        response = await auth_client.get("/api/v1/games/")

        assert response.status_code == 200
        data = response.json()
        assert any(g["title"] == "Test Game" for g in data)

    async def test_list_games_search(self, auth_client: AsyncClient):
        """Search filters games by title."""
        # Create category
        category_payload = {
            "name": "Search Category",
            "slug": "search-category",
        }
        category_resp = await auth_client.post("/api/v1/games/categories", json=category_payload)
        category_id = category_resp.json()["id"]

        # Create games
        for title in ["Dragons Quest", "Dungeon Crawl", "Space Adventure"]:
            game_payload = {
                "title": title,
                "category_id": category_id,
                "min_players": 2,
                "max_players": 4,
            }
            await auth_client.post("/api/v1/games/", json=game_payload)

        # Search for "Dungeon"
        response = await auth_client.get("/api/v1/games/?q=Dungeon")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any("Dungeon" in g["title"] for g in data)
        assert not any("Space" in g["title"] for g in data)

    async def test_list_games_filter_by_category(self, auth_client: AsyncClient):
        """Filter games by category."""
        # Create two categories
        rpg_resp = await auth_client.post(
            "/api/v1/games/categories",
            json={"name": "RPG Filter", "slug": "rpg-filter"},
        )
        rpg_id = rpg_resp.json()["id"]

        board_resp = await auth_client.post(
            "/api/v1/games/categories",
            json={"name": "Board Filter", "slug": "board-filter"},
        )
        board_id = board_resp.json()["id"]

        # Create games in each category
        await auth_client.post(
            "/api/v1/games/",
            json={"title": "RPG Game", "category_id": rpg_id, "min_players": 3, "max_players": 6},
        )
        await auth_client.post(
            "/api/v1/games/",
            json={"title": "Board Game", "category_id": board_id, "min_players": 2, "max_players": 4},
        )

        # Filter by RPG category
        response = await auth_client.get(f"/api/v1/games/?category_id={rpg_id}")

        assert response.status_code == 200
        data = response.json()
        assert all(g["category_id"] == rpg_id for g in data)

    async def test_list_games_pagination(self, auth_client: AsyncClient):
        """Pagination works correctly."""
        # Create category
        category_payload = {
            "name": "Pagination Category",
            "slug": "pagination-category",
        }
        category_resp = await auth_client.post("/api/v1/games/categories", json=category_payload)
        category_id = category_resp.json()["id"]

        # Create 5 games
        for i in range(5):
            game_payload = {
                "title": f"Pagination Game {i}",
                "category_id": category_id,
                "min_players": 2,
                "max_players": 4,
            }
            await auth_client.post("/api/v1/games/", json=game_payload)

        # Get first 2
        response1 = await auth_client.get("/api/v1/games/?limit=2&offset=0")
        assert response1.status_code == 200
        data1 = response1.json()
        assert len(data1) == 2

        # Get next 2
        response2 = await auth_client.get("/api/v1/games/?limit=2&offset=2")
        assert response2.status_code == 200
        data2 = response2.json()
        assert len(data2) == 2

        # Different games
        ids1 = {g["id"] for g in data1}
        ids2 = {g["id"] for g in data2}
        assert ids1.isdisjoint(ids2)


class TestCreateGame:
    """Tests for POST /api/v1/games/"""

    async def test_create_game_success(self, auth_client: AsyncClient):
        """Create returns 201 with created entity."""
        # Create category first
        category_payload = {
            "name": "Create Game Category",
            "slug": "create-game-category",
        }
        category_resp = await auth_client.post("/api/v1/games/categories", json=category_payload)
        category_id = category_resp.json()["id"]

        # Create game
        payload = {
            "title": "New Game",
            "category_id": category_id,
            "publisher": "Game Publisher",
            "description": "A great game",
            "complexity": "INTERMEDIATE",
            "min_players": 2,
            "max_players": 5,
        }

        response = await auth_client.post("/api/v1/games/", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Game"
        assert data["publisher"] == "Game Publisher"
        assert data["complexity"] == "INTERMEDIATE"
        assert data["min_players"] == 2
        assert data["max_players"] == 5
        assert "id" in data
        assert "created_at" in data

    async def test_create_game_unauthorized(self, client: AsyncClient):
        """Create without auth returns 401."""
        payload = {
            "title": "Unauthorized Game",
            "category_id": "00000000-0000-0000-0000-000000000000",
            "min_players": 2,
            "max_players": 4,
        }

        response = await client.post("/api/v1/games/", json=payload)
        assert response.status_code == 401

    async def test_create_game_invalid_category(self, auth_client: AsyncClient):
        """Create with non-existent category returns 400."""
        payload = {
            "title": "Game with Bad Category",
            "category_id": "00000000-0000-0000-0000-000000000000",
            "min_players": 2,
            "max_players": 4,
        }

        response = await auth_client.post("/api/v1/games/", json=payload)
        assert response.status_code == 400
        assert "Category not found" in response.json()["detail"]

    async def test_create_game_invalid_players(self, auth_client: AsyncClient):
        """Create with min > max players returns 422."""
        # Create category first
        category_payload = {
            "name": "Invalid Players Category",
            "slug": "invalid-players-category",
        }
        category_resp = await auth_client.post("/api/v1/games/categories", json=category_payload)
        category_id = category_resp.json()["id"]

        payload = {
            "title": "Invalid Players Game",
            "category_id": category_id,
            "min_players": 6,
            "max_players": 2,  # Less than min
        }

        response = await auth_client.post("/api/v1/games/", json=payload)
        assert response.status_code == 422


class TestGetGame:
    """Tests for GET /api/v1/games/{id}"""

    async def test_get_game_success(self, auth_client: AsyncClient):
        """Get existing game returns 200."""
        # Create category first
        category_payload = {
            "name": "Get Game Category",
            "slug": "get-game-category",
        }
        category_resp = await auth_client.post("/api/v1/games/categories", json=category_payload)
        category_id = category_resp.json()["id"]

        # Create game
        payload = {
            "title": "Get Test Game",
            "category_id": category_id,
            "min_players": 2,
            "max_players": 4,
        }
        create_response = await auth_client.post("/api/v1/games/", json=payload)
        game_id = create_response.json()["id"]

        # Get it
        response = await auth_client.get(f"/api/v1/games/{game_id}")

        assert response.status_code == 200
        assert response.json()["title"] == "Get Test Game"

    async def test_get_game_not_found(self, client: AsyncClient):
        """Get non-existent game returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = await client.get(f"/api/v1/games/{fake_id}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Game not found"
