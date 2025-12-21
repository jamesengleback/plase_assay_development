import pytest


def test_get_results_no_filters(client, test_data):
    response = client.get("/result/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert all("id" in result for result in data)


def test_get_result_by_id(client, test_data):
    response = client.get("/result/?id=1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["experiment_id"] == 1


def test_get_result_by_id_not_found(client, test_data):
    response = client.get("/result/?id=999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_filter_by_experiment_id(client, test_data):
    response = client.get("/result/?experiment_id=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(r["experiment_id"] == 1 for r in data)


def test_filter_by_locked(client, test_data):
    response = client.get("/result/?locked=true")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["locked"] is True

    response = client.get("/result/?locked=false")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(r["locked"] is False for r in data)


def test_filter_by_accepted(client, test_data):
    response = client.get("/result/?accepted=true")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(r["accepted"] is True for r in data)


def test_filter_by_protein(client, test_data):
    response = client.get("/result/?protein=BM3%20WT")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(r["protein"]["name"] == "BM3 WT" for r in data)


def test_filter_by_well_volume_min_max(client, test_data):
    response = client.get("/result/?well_volume_min=60&well_volume_max=80")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == 3  # result3 linked to well3 with volume 75


def test_filter_by_protein_concentration_min_max(client, test_data):
    response = client.get("/result/?protein_concentration_min=1.5&protein_concentration_max=2.5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(1.5 <= r["protein_concentration"] <= 2.5 for r in data)


def test_search_by_id(client, test_data):
    response = client.get("/result/?search=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == 1


def test_search_by_compound_name(client, test_data):
    response = client.get("/result/?search=Compound%20X")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(r["compound"]["name"] == "Compound X" for r in data)


def test_pagination(client, test_data):
    response = client.get("/result/?page=1&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    response = client.get("/result/?page=2&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


def test_combined_filters(client, test_data):
    response = client.get("/result/?experiment_id=1&accepted=true&protein_concentration_min=0.5&protein_concentration_max=1.5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == 1


def test_no_results(client, test_data):
    response = client.get("/result/?experiment_id=999")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0


def test_edge_case_empty_search(client, test_data):
    response = client.get("/result/?search=nonexistent")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0