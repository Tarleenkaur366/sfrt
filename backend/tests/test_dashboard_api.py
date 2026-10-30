def test_dashboard_endpoints(client, test_user, auth_headers):
    # Add transaction
    payload = {
        "transaction_date": "2026-06-01",
        "description": "Monthly Product Subscription",
        "transaction_type": "Revenue",
        "amount": 50000.00,
        "currency": "INR"
    }
    client.post("/api/v1/transactions", json=payload, headers=auth_headers)

    res_summary = client.get("/api/v1/dashboard/summary", headers=auth_headers)
    assert res_summary.status_code == 200
    data = res_summary.json()
    assert data["total_income"] == 50000.00
    assert data["total_transactions"] == 1

    res_trends = client.get("/api/v1/dashboard/trends", headers=auth_headers)
    assert res_trends.status_code == 200
    assert "income" in res_trends.json()

    res_cats = client.get("/api/v1/dashboard/category-distribution?category_type=INCOME", headers=auth_headers)
    assert res_cats.status_code == 200
