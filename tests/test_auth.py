def test_protected_endpoint_requires_token(client):
    assert client.get('/api/v1/orders').status_code in (401,403)
