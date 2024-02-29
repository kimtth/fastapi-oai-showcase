from datetime import datetime
import os
from typing import Dict, List, Optional
import uvicorn
from fastapi import Body, FastAPI, APIRouter, HTTPException
from fastapi import Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import llm_util
import logging

load_dotenv()

current_file_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file_path)

# Create the filename string
date_string = datetime.now().strftime('%y%m%d')
filename = f'logging_{date_string}.log'
log_file_path = os.path.join(current_dir, filename)

for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file_path, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# sqlite:///relative/path/to/file.db
DATABASE_URL = f'sqlite:///./demo.db'
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Define SQLAlchemy ORM models


class ChatRoom(Base):
    __tablename__ = 'ChatRoom'
    seq = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id = Column(String, nullable=False, unique=True)
    name = Column(String)
    prompt = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(),
                        onupdate=func.now())
    # One-to-Many relationship: One chat room can have many messages
    messages = relationship('Message', backref='chat_room', cascade="all,delete")


class Message(Base):
    __tablename__ = 'Message'
    seq = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id = Column(String, nullable=False, unique=True)
    chat_id = Column(String, ForeignKey('ChatRoom.id', ondelete="CASCADE"))
    # Note: 'from' is a reserved keyword in SQL
    from_who = Column(String, nullable=False)
    msg = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(),
                        onupdate=func.now())


class Code(Base):
    __tablename__ = 'Code'
    seq = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id = Column(String, nullable=False, unique=True)
    category = Column(String, nullable=False)
    value = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(),
                        onupdate=func.now())


# Create the database tables
Base.metadata.create_all(bind=engine)

# FastAPI specific code
app = FastAPI()

router = APIRouter(prefix="/api")

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request and response


class MessageCreate(BaseModel):
    id: str
    from_who: str
    msg: str


class MessageDisplay(BaseModel):
    id: str
    chat_id: str
    from_who: Optional[str]
    msg: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChatRoomCreate(BaseModel):
    id: str
    name: str
    prompt: str = None


class ChatRoomDisplay(BaseModel):
    id: str
    name: str
    prompt: Optional[str] = None
    # Set messages as an optional field
    messages: Optional[List[MessageDisplay]] = []
    # messages: list[MessageDisplay] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CodeDisplay(BaseModel):
    id: str
    category: str
    value: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Dependency to get the database session


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
async def health_check():
    return {"message": "OK!"}


@router.get("/")
async def router_health_check():
    return {"message": "router OK!"}


# add get endpoint for EntityIntent
@router.get("/code/{category}", response_model=list[CodeDisplay])
async def fetch_entity_intent(category: str, db: Session = Depends(get_db)):
    # filtered by category
    return db.query(Code).filter(Code.category == category).all()


# Endpoints for chatroom and message operations
@router.post("/chat", response_model=ChatRoomDisplay)
async def add_chatroom(chat: ChatRoomCreate, db: Session = Depends(get_db)):
    db_chatroom = ChatRoom(id=chat.id, name=chat.name, prompt=chat.prompt)
    db.add(db_chatroom)
    db.commit()
    db.refresh(db_chatroom)
    return db_chatroom


@router.get("/chat", response_model=list[ChatRoomDisplay])
async def fetch_chats(db: Session = Depends(get_db)):
    # db query to fetch all chatrooms without messages
    # add a condition for orderby created_at
    return db.query(ChatRoom).order_by(ChatRoom.created_at.desc()).all()    


@router.get("/chat/{chat_id}", response_model=ChatRoomDisplay)
async def fetch_chat(chat_id: str, db: Session = Depends(get_db)):
    db_chatroom = db.query(ChatRoom).filter(ChatRoom.id == chat_id).first()
    if db_chatroom is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    return db_chatroom


@router.put("/chat/{chat_id}", response_model=ChatRoomDisplay)
async def update_chat(chat_id: str, chat: ChatRoomCreate, db: Session = Depends(get_db)):
    db_chatroom = db.query(ChatRoom).filter(ChatRoom.id == chat_id).first()
    if db_chatroom is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    db_chatroom.name = chat.name
    db_chatroom.prompt = chat.prompt
    db.commit()
    db.refresh(db_chatroom)
    return db_chatroom


@router.delete("/chat/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chatroom(chat_id: str, db: Session = Depends(get_db)):
    db_chatroom = db.query(ChatRoom).filter(ChatRoom.id == chat_id).first()
    if db_chatroom is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    db.delete(db_chatroom)
    db.commit()
    return {"message": "ChatRoom deleted successfully"}


@router.post("/chat/{chat_id}/message", response_model=MessageDisplay)
async def add_message(chat_id: str, message: MessageCreate, db: Session = Depends(get_db)):
    db_message = Message(
        chat_id=chat_id, id=message.id, from_who=message.from_who, msg=message.msg)
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message


@router.get("/chat/{chat_id}/message", response_model=list[MessageDisplay])
async def fetch_messages(chat_id: str, db: Session = Depends(get_db)):
    db_chatroom = db.query(ChatRoom).filter(ChatRoom.id == chat_id).first()
    if db_chatroom is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    return db_chatroom.messages


@router.post("/chat/response")
async def llm_new_response(data: Dict[str, str] = Body(...), db: Session = Depends(get_db)):
    try:
        chat_id = data.get('chat_id')
        message = data.get('msg')
        mode = data.get('mode')
        if message is None or mode is None:
            raise HTTPException(status_code=400, detail="Message or mode is missing")
        # TODO: Call the LLM model to get the response
        # TODO: Enum mode == 'gpt' or 'work'

        if mode == 'gpt':
            system_msg = "You are an AI assistant that helps people find information."
            # resp = llm_util.send_request_to_chatgpt(system_msg, message)
            db_chatroom = db.query(ChatRoom).filter(ChatRoom.id == chat_id).first()
            if db_chatroom is None:
                raise HTTPException(status_code=404, detail="Chat not found")
            
            message_history = []
            for msg in db_chatroom.messages:
                # chat_id
                if msg.from_who == 'me':
                    message_history.append({"role": "user", "content": msg.msg})
                elif msg.from_who == 'computer':
                    message_history.append({"role": "assistant", "content": msg.msg})
            resp = llm_util.send_request_to_chatgpt_with_history(system_msg, message, message_history)
        else:
            resp = llm_util.planning_for_response(message)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Register the API router
# root_path: http://127.0.0.1:5000/api
app.include_router(router)

if __name__ == '__main__':
    if os.getenv('ENV_MODE') == 'dev':
        # app:app == filename:app <= FastAPI()
        uvicorn.run(app='app:app', host="127.0.0.1", port=5000)
    else:
        # Azure App service uses 8000 as default port internally.
        uvicorn.run(app='app:app', host="0.0.0.0", workers=4)
