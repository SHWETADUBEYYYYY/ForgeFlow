import os
import sqlite3
import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

ROOT = Path(__file__).resolve().parent.parent
MAX_UPLOAD_BYTES = 50 * 1024 * 1024
AUDIO_TYPES = {'.mp3': 'audio/mpeg', '.wav': 'audio/wav', '.ogg': 'audio/ogg'}


def create_app(data_dir=None):
    storage = Path(data_dir or os.environ.get('MUSIC_DATA_DIR', ROOT / 'data'))
    uploads = storage / 'uploads'
    uploads.mkdir(parents=True, exist_ok=True)
    database = storage / 'music.sqlite3'

    def connect():
        connection = sqlite3.connect(database)
        connection.row_factory = sqlite3.Row
        return connection

    with connect() as connection:
        connection.execute('CREATE TABLE IF NOT EXISTS tracks (id TEXT PRIMARY KEY, name TEXT NOT NULL, filename TEXT NOT NULL, media_type TEXT NOT NULL, size INTEGER NOT NULL)')

    app = FastAPI(title='Simple Music Player')

    @app.get('/')
    def home():
        return FileResponse(ROOT / 'frontend' / 'index.html')

    @app.get('/api/tracks')
    def list_tracks():
        with connect() as connection:
            rows = connection.execute('SELECT id, name, size FROM tracks ORDER BY rowid').fetchall()
        return [dict(row) for row in rows]

    @app.post('/api/tracks', status_code=201)
    async def upload_track(file: UploadFile = File(...)):
        # Original names are display-only; generated names select storage paths.
        name = (file.filename or '').replace('\\', '/').split('/')[-1]
        extension = Path(name).suffix.lower()
        if extension not in AUDIO_TYPES:
            await file.close()
            raise HTTPException(400, 'Choose an MP3, WAV, or OGG file.')
        # Multipart parsing already measured the file; reject before copying it.
        # Keep the streaming check below as a fallback when size is unknown.
        if file.size is not None and file.size > MAX_UPLOAD_BYTES:
            await file.close()
            raise HTTPException(413, 'Each audio file must be 50 MB or smaller.')
        track_id = uuid.uuid4().hex
        filename = track_id + extension
        destination = uploads / filename
        size = 0
        try:
            with destination.open('xb') as output:
                while chunk := await file.read(1024 * 1024):
                    size += len(chunk)
                    if size > MAX_UPLOAD_BYTES:
                        raise HTTPException(413, 'Each audio file must be 50 MB or smaller.')
                    output.write(chunk)
            if size == 0:
                raise HTTPException(400, 'The audio file is empty.')
            with connect() as connection:
                connection.execute('INSERT INTO tracks VALUES (?, ?, ?, ?, ?)',
                                   (track_id, name, filename, AUDIO_TYPES[extension], size))
        except Exception:
            destination.unlink(missing_ok=True)
            raise
        finally:
            await file.close()
        return {'id': track_id, 'name': name, 'size': size}

    @app.get('/api/tracks/{track_id}/audio')
    def audio(track_id: str):
        with connect() as connection:
            row = connection.execute('SELECT filename, media_type FROM tracks WHERE id = ?', (track_id,)).fetchone()
        if row is None or not (uploads / row['filename']).is_file():
            raise HTTPException(404, 'Track not found.')
        return FileResponse(uploads / row['filename'], media_type=row['media_type'])

    return app


app = create_app()
