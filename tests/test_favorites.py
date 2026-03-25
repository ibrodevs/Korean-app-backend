import pytest
from favorites.models import Favorite


@pytest.mark.django_db
class TestFavoritesList:
    def test_list_requires_auth(self, api_client):
        resp = api_client.get("/api/v1/favorites/")
        assert resp.status_code == 401

    def test_list_empty_for_new_user(self, auth_client):
        resp = auth_client.get("/api/v1/favorites/")
        assert resp.status_code == 200
        assert resp.data["count"] == 0
        assert resp.data["results"] == []

    def test_list_returns_own_favorites(self, auth_client, user, product):
        Favorite.objects.create(user=user, product=product)
        resp = auth_client.get("/api/v1/favorites/")
        assert resp.status_code == 200
        assert resp.data["count"] == 1
        assert resp.data["results"][0]["product"]["id"] == product.id

    def test_list_does_not_return_other_users_favorites(self, auth_client, admin_user, product):
        # admin_user adds product to favorites
        Favorite.objects.create(user=admin_user, product=product)
        # auth_client (regular user) should see empty list
        resp = auth_client.get("/api/v1/favorites/")
        assert resp.status_code == 200
        assert resp.data["count"] == 0


@pytest.mark.django_db
class TestFavoritesAdd:
    def test_add_requires_auth(self, api_client, product):
        resp = api_client.post("/api/v1/favorites/", {"product_id": product.id})
        assert resp.status_code == 401

    def test_add_success(self, auth_client, product):
        resp = auth_client.post("/api/v1/favorites/", {"product_id": product.id})
        assert resp.status_code == 201
        assert resp.data["product"]["id"] == product.id

    def test_add_duplicate_forbidden(self, auth_client, user, product):
        Favorite.objects.create(user=user, product=product)
        resp = auth_client.post("/api/v1/favorites/", {"product_id": product.id})
        assert resp.status_code == 400
        assert "detail" in resp.data

    def test_add_nonexistent_product(self, auth_client):
        resp = auth_client.post("/api/v1/favorites/", {"product_id": 99999})
        assert resp.status_code == 404

    def test_add_creates_db_record(self, auth_client, user, product):
        auth_client.post("/api/v1/favorites/", {"product_id": product.id})
        assert Favorite.objects.filter(user=user, product=product).exists()


@pytest.mark.django_db
class TestFavoritesDelete:
    def test_delete_requires_auth(self, api_client, product):
        resp = api_client.delete(f"/api/v1/favorites/{product.id}/")
        assert resp.status_code == 401

    def test_delete_success(self, auth_client, user, product):
        Favorite.objects.create(user=user, product=product)
        resp = auth_client.delete(f"/api/v1/favorites/{product.id}/")
        assert resp.status_code == 204
        assert not Favorite.objects.filter(user=user, product=product).exists()

    def test_delete_not_found(self, auth_client, product):
        resp = auth_client.delete(f"/api/v1/favorites/{product.id}/")
        assert resp.status_code == 404

    def test_cannot_delete_other_users_favorite(self, auth_client, admin_user, product):
        # admin adds to favorites, regular user tries to delete
        Favorite.objects.create(user=admin_user, product=product)
        resp = auth_client.delete(f"/api/v1/favorites/{product.id}/")
        assert resp.status_code == 404
        # still exists in DB
        assert Favorite.objects.filter(user=admin_user, product=product).exists()
