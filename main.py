from datetime import datetime
from typing import Optional

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator

app = FastAPI()

router = APIRouter(prefix="/v1")

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
    id: str
    from_field: str = Field(None, alias='from')  # from: str
    text: str
    created_at: Optional[datetime] = datetime.now()

    @validator("created_at", pre=True)
    def parse_timestamp(cls, value):
        return datetime.strftime(
            value,
            "%Y-%m-%dT%H:%M:%S.%fZ"
        )


class Chat(BaseModel):
    id: str
    name: str
    messages: list[Message]
    created_at: Optional[datetime] = datetime.now()  # Optional[str] is the same as str | None

    @validator("created_at", pre=True)
    def parse_timestamp(cls, value):
        return datetime.strftime(
            value,
            "%Y-%m-%dT%H:%M:%S.%fZ"
        )


@app.get("/")
async def health_check():
    return {"message": "OK!"}


@router.get("/")
async def health_check():
    return {"message": "router OK!"}


@app.get("/chat/{chat_id}")
async def fetch_messages(chat_id: str):
    return {"message": chat_id}


@app.patch("/chat/{chat_id}")
async def update_chat(chat_id: str, chat: Chat):
    return {"message": chat_id, "body": chat.json()}


@app.post("/chat/{chat_id}/message")
async def add_message(chat_id: str, message: Message):
    return {"message": chat_id, "body": message.json()}


@app.post("/chat")
async def add_chatroom():
    chat_id = 'test'
    return {"message": chat_id}


@app.delete("/chat/{chat_id}/")
async def delete_chatroom(chat_id: str):
    return {"message": chat_id}


# root_path: http://127.0.0.1:5000/api
app.mount("/api", app)
app.include_router(router)
