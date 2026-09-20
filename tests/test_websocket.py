import asyncio
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.api.proposed import communication


async def test_websocket_authentication_and_persistence(env, monkeypatch):
    c, factory, users, h, _ = env
    monkeypatch.setattr(communication, 'AsyncSessionLocal', factory)
    created = await c.post('/api/v1/conversations', json={'other_user_id': users['alumni']}, headers=h['student'])
    cid = created.json()['conversation_id']
    def socket_exchange():
        with TestClient(app) as client:
            with client.websocket_connect(f'/api/v1/ws/conversations/{cid}') as socket:
                socket.send_json({'token': h['student']['Authorization'].split(' ', 1)[1]})
                assert socket.receive_json()['type'] == 'history'
                socket.send_json({'body': 'Persistent WebSocket message'})
                received = socket.receive_json()
                assert received['type'] == 'message'
                assert received['body'] == 'Persistent WebSocket message'
    # SQLite's test connection supports this thread bridge; asyncpg is loop-bound.
    import os
    if os.getenv('TEST_DATABASE_URL'):
        pytest.skip('Thread-bridged WebSocket test uses SQLite; asyncpg is event-loop bound')
    await asyncio.to_thread(socket_exchange)
    result = await c.get(f'/api/v1/conversations/{cid}/messages', headers=h['alumni'])
    assert result.json()[0]['body'] == 'Persistent WebSocket message'
