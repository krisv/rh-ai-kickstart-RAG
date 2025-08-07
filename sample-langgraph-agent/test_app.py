import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_submit_idea(client):
    """Test that submitting an idea returns a 200 status code."""
    response = client.post('/do_something', data={'name': 'Matt Bellamy'})
    assert response.status_code == 200
    assert response.json == {'status': 'Processing started'}
