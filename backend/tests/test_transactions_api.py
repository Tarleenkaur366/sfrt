def test_transaction_crud_and_isolation(client, test_user, auth_headers, other_user, other_auth_headers):
    # 1. Create transaction as test_user
    payload = {
        "transaction_date": "2026-06-15",
        "description": "Enterprise Software Consulting",
        "transaction_type": "Revenue",
        "amount": 75000.00,
        "currency": "INR",
        "payment_method": "Bank Transfer",
        "reference_number": "INV-2026-001"
    }
    create_res = client.post("/api/v1/transactions", json=payload, headers=auth_headers)
    assert create_res.status_code == 201
    tx_data = create_res.json()
    tx_id = tx_data["id"]
    assert tx_data["description"] == payload["description"]
    assert float(tx_data["amount"]) == 75000.00

    # 2. List transactions for test_user
    list_res = client.get("/api/v1/transactions", headers=auth_headers)
    assert list_res.status_code == 200
    assert list_res.json()["total"] == 1
    assert list_res.json()["items"][0]["id"] == tx_id

    # 3. User Data Isolation: other_user cannot see test_user's transaction
    other_list = client.get("/api/v1/transactions", headers=other_auth_headers)
    assert other_list.status_code == 200
    assert other_list.json()["total"] == 0

    other_get = client.get(f"/api/v1/transactions/{tx_id}", headers=other_auth_headers)
    assert other_get.status_code == 404

    other_del = client.delete(f"/api/v1/transactions/{tx_id}", headers=other_auth_headers)
    assert other_del.status_code == 404

    # 4. Update transaction as test_user
    update_res = client.patch(
        f"/api/v1/transactions/{tx_id}",
        json={"amount": 80000.00, "description": "Updated Consulting Contract"},
        headers=auth_headers
    )
    assert update_res.status_code == 200
    assert float(update_res.json()["amount"]) == 80000.00

    # 5. Export CSV
    export_res = client.get("/api/v1/transactions/export/csv", headers=auth_headers)
    assert export_res.status_code == 200
    assert "text/csv" in export_res.headers["content-type"]
    assert "Updated Consulting Contract" in export_res.text

    # 6. Delete transaction as test_user
    del_res = client.delete(f"/api/v1/transactions/{tx_id}", headers=auth_headers)
    assert del_res.status_code == 200

    get_again = client.get(f"/api/v1/transactions/{tx_id}", headers=auth_headers)
    assert get_again.status_code == 404
