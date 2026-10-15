import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_frontend():
    response = client.get('/')
    assert response.status_code == 200
    assert 'text/html' in response.headers['content-type']
    for text in ['BMI calculator', 'Height', 'Weight', 'Calculate BMI', 'not intended for children or pregnancy']:
        assert text in response.text


def test_metric_calculation():
    response = client.post('/api/bmi', json={'height_cm': 170, 'weight_kg': 65})
    assert response.status_code == 200
    assert response.json() == {'bmi': 22.5, 'category': 'Normal weight'}


@pytest.mark.parametrize('bmi,category', [
    (18.49, 'Underweight'), (18.5, 'Normal weight'),
    (24.99, 'Normal weight'), (25, 'Overweight'),
    (29.99, 'Overweight'), (30, 'Obesity'),
])
def test_category_before_rounding(bmi, category):
    response = client.post('/api/bmi', json={'height_cm': 200, 'weight_kg': bmi * 4})
    assert response.status_code == 200
    assert response.json() == {'bmi': round(bmi, 1), 'category': category}


def test_decimal_measurements():
    response = client.post('/api/bmi', json={'height_cm': 172.5, 'weight_kg': 66.3})
    assert response.status_code == 200
    assert response.json()['bmi'] == round(66.3 / 1.725 ** 2, 1)


@pytest.mark.parametrize('field', ['height_cm', 'weight_kg'])
@pytest.mark.parametrize('value', ['', 'abc', 0, -1, None, 'NaN', 'Infinity', '-Infinity'])
def test_invalid_measurements(field, value):
    payload = {'height_cm': 170, 'weight_kg': 65}
    payload[field] = value
    response = client.post('/api/bmi', json=payload)
    assert response.status_code == 422
    assert isinstance(response.json()['detail'], list)


@pytest.mark.parametrize('payload', ['{}', '{"height_cm":NaN,"weight_kg":65}', '{"height_cm":170,"weight_kg":Infinity}'])
def test_missing_and_nonfinite_json(payload):
    response = client.post('/api/bmi', content=payload, headers={'Content-Type': 'application/json'})
    assert response.status_code == 422
    assert isinstance(response.json()['detail'], list)


@pytest.mark.parametrize('height,weight', [(1e-320, 65), (1e308, 1e-308)])
def test_uncalculable_values(height, weight):
    response = client.post('/api/bmi', json={'height_cm': height, 'weight_kg': weight})
    assert response.status_code == 422
    assert isinstance(response.json()['detail'], list)
