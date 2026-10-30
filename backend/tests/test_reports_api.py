def test_report_generation_and_export_api(client, test_user, auth_headers):
    # Add revenue transaction
    payload = {
        "transaction_date": "2026-07-01",
        "description": "Enterprise Licensing",
        "transaction_type": "Revenue",
        "amount": 120000.00,
        "currency": "INR"
    }
    client.post("/api/v1/transactions", json=payload, headers=auth_headers)

    gen_payload = {
        "report_type": "INCOME_EXPENSE",
        "title": "H2 Income and Expense Overview",
        "start_date": "2026-07-01",
        "end_date": "2026-07-31",
        "currency": "INR"
    }
    gen_res = client.post("/api/v1/reports/generate", json=gen_payload, headers=auth_headers)
    assert gen_res.status_code == 201
    rep_data = gen_res.json()
    rep_id = rep_data["id"]
    assert rep_data["title"] == "H2 Income and Expense Overview"

    # Export as PDF
    pdf_res = client.get(f"/api/v1/reports/{rep_id}/export?format=pdf", headers=auth_headers)
    assert pdf_res.status_code == 200
    assert "application/pdf" in pdf_res.headers["content-type"]
    assert len(pdf_res.content) > 500  # PDF content generated

    # Export as CSV
    csv_res = client.get(f"/api/v1/reports/{rep_id}/export?format=csv", headers=auth_headers)
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers["content-type"]
    assert "H2 Income and Expense Overview" in csv_res.text
