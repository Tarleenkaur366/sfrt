def test_register_and_login_success(client):
    reg_payload = {
        "full_name": "Alice Finance",
        "email": "alice@example.com",
        "password": "Password123!",
        "business_name": "Alice Advisory",
        "default_currency": "INR"
    }
    res_reg = client.post("/api/v1/auth/register", json=reg_payload)
    assert res_reg.status_code == 201
    reg_data = res_reg.json()
    assert reg_data["user"]["email"] == "alice@example.com"
    assert "token" in reg_data

    # Duplicate registration check
    res_dup = client.post("/api/v1/auth/register", json=reg_payload)
    assert res_dup.status_code == 400
    assert "already exists" in res_dup.json()["detail"]

    # Login check
    login_payload = {
        "email": "alice@example.com",
        "password": "Password123!"
    }
    res_login = client.post("/api/v1/auth/login", json=login_payload)
    assert res_login.status_code == 200
    assert res_login.json()["token"] is not None

def test_unauthorized_access(client):
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401

def test_get_me_with_token(client, test_user, auth_headers):
    res = client.get("/api/v1/auth/me", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["email"] == test_user.email
