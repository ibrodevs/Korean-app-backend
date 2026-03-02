import requests

BASE_URL = "http://localhost:8000/api/v1"


def test_products_list_basic_smoke():
    """
    Integration smoke-test for GET /api/v1/products/ with pagination.
    Requires the Django dev server to be running.
    """
    res = requests.get(f"{BASE_URL}/products/", timeout=5)

    assert res.status_code == 200
    data = res.json()

    assert "results" in data
    assert "next" in data
    assert "previous" in data


def test_products_list_supports_language_param():
    params_en = {
        "lang": "en",
    }
    res_en = requests.get(f"{BASE_URL}/products/", params=params_en, timeout=5)
    assert res_en.status_code == 200
    data_en = res_en.json()
    assert "results" in data_en

    params_ru = {
        # lang omitted -> defaults to ru
    }
    res_ru = requests.get(f"{BASE_URL}/products/", params=params_ru, timeout=5)
    assert res_ru.status_code == 200
    data_ru = res_ru.json()
    assert "results" in data_ru


def test_catalog_search_endpoint_exists():
    res = requests.get(f"{BASE_URL}/catalog-search/", timeout=5)
    assert res.status_code == 200
    data = res.json()
    assert "results" in data
    assert "facets" in data


def test_reference_endpoints_exist():
    categories_res = requests.get(f"{BASE_URL}/categories/", timeout=5)
    brands_res = requests.get(f"{BASE_URL}/brands/", timeout=5)

    assert categories_res.status_code == 200
    assert brands_res.status_code == 200
