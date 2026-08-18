import httpx
import pytest


@pytest.mark.behaviour("accounts.creation.created_account_appears_in_the_list")
def test_created_account_appears_in_the_list(client, unique):
    name = unique("account")

    created = client.post("/accounts", json={"name": name, "currency": "EUR"})
    assert created.status_code == 201, f"POST /accounts returned {created.status_code}: {created.text}"
    identifier = created.json()["id"]

    listed = client.get("/accounts")
    assert listed.status_code == 200, f"GET /accounts returned {listed.status_code}: {listed.text}"

    matching = [account for account in listed.json()["accounts"] if account["id"] == identifier]
    assert matching, f"account {identifier} named {name!r} was created but is absent from GET /accounts"
    assert matching[0]["name"] == name


@pytest.mark.behaviour("accounts.listing.requires_authentication")
def test_listing_accounts_requires_authentication(base_url):
    with httpx.Client(base_url=base_url, timeout=30.0) as anonymous:
        response = anonymous.get("/accounts")

    assert response.status_code == 401, f"GET /accounts without a session returned {response.status_code}: {response.text}"
