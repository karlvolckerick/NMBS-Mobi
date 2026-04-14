def test_status_returns_ok(client):
    """Test that startup probe returns ok status."""
    # Arrange
    endpoint = "/status"
    expected_status_code = 200
    expected_body = "OK"

    # Act
    response = client.get(endpoint)

    # Assert
    assert response.status_code == expected_status_code
    assert response.json() == expected_body
