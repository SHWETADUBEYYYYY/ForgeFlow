import io
import wave

import pytest
from fastapi.testclient import TestClient

from backend.main import create_app


def wav_bytes():
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(8000)
        audio.writeframes(b'\x00\x00' * 800)
    return buffer.getvalue()


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path)) as session:
        yield session


def test_home_and_empty_library(client):
    page = client.get('/')
    assert page.status_code == 200
    assert 'Add Music' in page.text
    assert '<audio' in page.text
    assert 'No music yet' in page.text
    assert client.get('/api/tracks').json() == []


@pytest.mark.parametrize('extension,media_type', [
    ('mp3', 'audio/mpeg'), ('wav', 'audio/wav'), ('ogg', 'audio/ogg'),
])
def test_upload_and_retrieve(client, extension, media_type):
    # Validation is extension-based; decoding is delegated to the browser.
    content = wav_bytes()
    response = client.post('/api/tracks', files={'file': (f'song.{extension}', content)})
    assert response.status_code == 201
    track = response.json()
    assert track['name'] == f'song.{extension}'
    assert track['size'] == len(content)
    assert client.get('/api/tracks').json() == [track]
    audio = client.get(f"/api/tracks/{track['id']}/audio")
    assert audio.status_code == 200
    assert audio.content == content
    assert audio.headers['content-type'] == media_type


def test_persistence_duplicates_and_safe_names(tmp_path):
    content = wav_bytes()
    with TestClient(create_app(tmp_path)) as client:
        tracks = [client.post('/api/tracks', files={
            'file': ('../../<song>.wav', content)
        }).json() for _ in range(2)]
    assert tracks[0]['id'] != tracks[1]['id']
    assert all(track['name'] == '<song>.wav' for track in tracks)
    stored = list((tmp_path / 'uploads').iterdir())
    assert len(stored) == 2
    assert all(path.name.endswith('.wav') and '<' not in path.name for path in stored)
    with TestClient(create_app(tmp_path)) as restarted:
        assert restarted.get('/api/tracks').json() == tracks
        for track in tracks:
            assert restarted.get(f"/api/tracks/{track['id']}/audio").content == content


@pytest.mark.parametrize('name,content', [('song.txt', b'hello'), ('empty.wav', b'')])
def test_invalid_upload_leaves_no_files(client, tmp_path, name, content):
    response = client.post('/api/tracks', files={'file': (name, content)})
    assert response.status_code == 400
    assert response.json()['detail']
    assert client.get('/api/tracks').json() == []
    assert list((tmp_path / 'uploads').iterdir()) == []


def test_size_limit_and_existing_library(client, tmp_path):
    valid = client.post('/api/tracks', files={'file': ('keep.wav', wav_bytes())}).json()
    limit = 50 * 1024 * 1024
    oversized = client.post('/api/tracks', files={'file': ('large.mp3', b'x' * (limit + 1))})
    assert oversized.status_code == 413
    assert client.get('/api/tracks').json() == [valid]
    assert len(list((tmp_path / 'uploads').iterdir())) == 1
    boundary = client.post('/api/tracks', files={'file': ('boundary.mp3', b'x' * limit)})
    assert boundary.status_code == 201
    assert boundary.json()['size'] == limit


def test_oversized_upload_rejected_before_storage_write(client, tmp_path, monkeypatch):
    from pathlib import Path
    from backend import main

    monkeypatch.setattr(main, 'MAX_UPLOAD_BYTES', 1024)
    original_open = Path.open

    def guard_storage_open(path, *args, **kwargs):
        if path.parent == tmp_path / 'uploads':
            pytest.fail('Oversized uploads must not open a storage file')
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, 'open', guard_storage_open)
    response = client.post('/api/tracks', files={'file': ('large.mp3', b'x' * 1025)})
    assert response.status_code == 413
    assert '50 MB' in response.json()['detail']
    assert client.get('/api/tracks').json() == []
    assert list((tmp_path / 'uploads').iterdir()) == []


def test_missing_track_and_missing_file(client, tmp_path):
    assert client.get('/api/tracks/nonexistent/audio').status_code == 404
    track = client.post('/api/tracks', files={'file': ('song.wav', wav_bytes())}).json()
    next((tmp_path / 'uploads').iterdir()).unlink()
    assert client.get(f"/api/tracks/{track['id']}/audio").status_code == 404
