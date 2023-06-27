import os
from typing import Optional, Literal

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator

import sqlite3
from datetime import datetime

app = FastAPI()

router = APIRouter(prefix="/v1")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "demo.db")
connection = sqlite3.connect(db_path, check_same_thread=False)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

'''
For example FastAPI uses Annotated for data validation:
def read_items(q: Annotated[str, Query(max_length=50)])
'''


class Message(BaseModel):
    chat_id: int
    id: Optional[int]
    fromWho: Literal['me', 'computer'] = 'me'
    # from_field: str = Field(None, alias='from')  # from: str
    text: Optional[str] = '_'
    created_at: datetime
    updated_at: datetime


class Chat(BaseModel):
    id: Optional[int]
    name: str
    messages: Optional[list[Message]]
    created_at: datetime
    updated_at: datetime


@app.on_event("startup")
async def server_init():
    cursor = connection.cursor()
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Message (
                chat_id INTEGER,
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fromWho TEXT,
                text TEXT,
                created_at TEXT NOT NULL DEFAULT (DATETIME('now', 'localtime')),
                updated_at TEXT NOT NULL DEFAULT (DATETIME('now', 'localtime')),
                FOREIGN KEY (chat_id) REFERENCES Chat(id) ON DELETE CASCADE ON UPDATE CASCADE
            );
        ''')

        cursor.execute('''   
            CREATE TRIGGER IF NOT EXISTS trigger_message_updated_at AFTER UPDATE ON Message
            BEGIN
                UPDATE Message SET updated_at = DATETIME('now', 'localtime') WHERE rowid == NEW.rowid;
            END;
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Chat (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                created_at TEXT NOT NULL DEFAULT (DATETIME('now', 'localtime')),
                updated_at TEXT NOT NULL DEFAULT (DATETIME('now', 'localtime'))
            );
        ''')

        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS trigger_chat_updated_at AFTER UPDATE ON Chat
            BEGIN
                UPDATE Chat SET updated_at = DATETIME('now', 'localtime') WHERE rowid == NEW.rowid;
            END;
        ''')
        connection.commit()
    except Exception as e:
        print(e)
    finally:
        cursor.close()


@app.on_event("shutdown")
async def shutdown():
    connection.close()


@app.get("/")
async def health_check():
    return {"message": "OK!"}


@router.get("/")
async def health_check():
    return {"message": "router OK!"}


@app.get("/chat")
async def fetch_chat():
    cursor = connection.cursor()
    try:
        cursor.execute('SELECT * FROM Chat')
        results = cursor.fetchall()
        chats = []
        for result in results:
            chat_id = result[0]
            cursor.execute('SELECT * FROM Message WHERE chat_id=?', (chat_id,))
            msg_result = cursor.fetchall()
            msgs = [
                Message(chat_id=msg[0], id=msg[1], fromWho=msg[2], text=msg[3], created_at=msg[4], updated_at=msg[5])
                for msg in msg_result]

            chat = Chat(id=result[0], name=result[1], messages=msgs, created_at=result[2], updated_at=result[3])
            chats.append(chat)
        return chats
    except Exception as e:
        return {"error": e}
    finally:
        cursor.close()


@app.get("/chat/{chat_id}")
async def fetch_messages(chat_id: str):
    cursor = connection.cursor()
    try:
        cursor.execute('SELECT * FROM Chat WHERE id=?', (chat_id,))
        result = cursor.fetchone()

        if result:
            cursor.execute('SELECT * FROM Message WHERE chat_id=? ORDER BY created_at ASC', (chat_id,))
            msg_result = cursor.fetchall()
            msgs = [
                Message(chat_id=msg[0], id=msg[1], fromWho=msg[2], text=msg[3], created_at=msg[4], updated_at=msg[5])
                for msg in msg_result]
            chat = Chat(id=result[0], name=result[1], messages=msgs, created_at=result[2], updated_at=result[3])
            return chat
        else:
            return {"error": "Chat not found"}
    except Exception as e:
        return {"error": e}
    finally:
        cursor.close()


# for updating the name of a chat room
@app.put("/chat/{chat_id}")
async def update_chat(chat_id: str, updated_chat: Chat):
    cursor = connection.cursor()
    try:
        cursor.execute('SELECT * FROM Chat WHERE id=?', (chat_id,))
        result = cursor.fetchone()
        if result:
            cursor.execute('UPDATE Chat SET name=? WHERE id=?', (
                updated_chat.name, chat_id
            ))
            connection.commit()
            return {"message": "Chat updated successfully"}
        else:
            return {"error": "Chat not found"}
    except Exception as e:
        return {"error": e}
    finally:
        cursor.close()


@app.post("/chat/{chat_id}/message")
async def add_message(chat_id: str, message: Message):
    cursor = connection.cursor()
    try:
        connection.execute('INSERT INTO Message(chat_id, id, fromWho, text) VALUES (?, ?, ?, ?)', (
            chat_id, message.id, message.fromWho, message.text
        ))
        connection.commit()
        return {"message": "Chat created successfully"}
    except Exception as e:
        return {"error": e}
    finally:
        cursor.close()


@app.post("/chat")
async def add_chatroom(chat: Chat):
    cursor = connection.cursor()
    try:
        rtn = cursor.execute('INSERT INTO Chat (id, name) VALUES (?, ?)', (
            chat.id, chat.name
        ))
        connection.commit()
        return {"message": "Chat created successfully {}".format(rtn)}
    except Exception as e:
        return {"error": e}
    finally:
        cursor.close()


@app.delete("/chat/{chat_id}")
async def delete_chatroom(chat_id: str):
    cursor = connection.cursor()
    try:
        cursor.execute('SELECT * FROM Chat WHERE id=?', (chat_id,))
        result = cursor.fetchone()
        if result:
            cursor.execute('DELETE FROM Chat WHERE id=?', (chat_id,))
            # cursor.execute('DELETE FROM Message WHERE chat_id=?', (chat_id,))
            connection.commit()
            return {"message": "Chat and Messages deleted successfully"}
        else:
            return {"error": "Chat not found"}
    except Exception as e:
        return {"error": e}
    finally:
        cursor.close()


# root_path: http://127.0.0.1:5000/api
app.mount("/api", app)
app.include_router(router)
