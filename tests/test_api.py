from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def payload(label="button", confidence=0.92, bbox=(10, 20, 110, 60)):
    return {
        "screenshot_width": 1280,
        "screenshot_height": 720,
        "detections": [{"label": label, "confidence": confidence, "bbox": bbox}],
    }


def test_health():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'


def test_classes():
    response = client.get('/classes')
    assert response.status_code == 200
    assert 'other_interactable' in response.json()['classes']


def test_valid_detection():
    response = client.post('/validate', json=payload())
    assert response.status_code == 200
    assert response.json()['valid'] is True
    assert response.json()['issues'] == []


def test_unknown_class():
    data = client.post('/validate', json=payload(label='mystery_widget')).json()
    assert data['valid'] is False
    assert data['issues'][0]['code'] == 'UNKNOWN_CLASS'


def test_out_of_bounds():
    data = client.post('/validate', json=payload(bbox=(5, 5, 1400, 70))).json()
    assert any(x['code'] == 'OUT_OF_BOUNDS' for x in data['issues'])


def test_box_order():
    data = client.post('/validate', json=payload(bbox=(150, 10, 30, 60))).json()
    assert any(x['code'] == 'INVALID_BOX_ORDER' for x in data['issues'])


def test_low_confidence():
    data = client.post('/validate', json=payload(confidence=0.1)).json()
    assert any(x['code'] == 'LOW_CONFIDENCE' for x in data['issues'])


def test_bad_request_rejected():
    data = payload(confidence=1.6)
    response = client.post('/validate', json=data)
    assert response.status_code == 422


def test_no_detections():
    data = payload()
    data['detections'] = []
    response = client.post('/validate', json=data)
    assert response.status_code == 200
    assert response.json()['detections_checked'] == 0
