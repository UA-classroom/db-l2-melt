# Add Pydantic schemas here that you'll use in your routes / endpoints
# Pydantic schemas are used to validate data that you receive, or to make sure that whatever data
# you send back to the client follows a certain structure
from typing import Optional

from pydantic import BaseModel

# Dessa måste finnas för att app.py inte ska krascha
# Tänk på dem som "formulär" som FastAPI använder.

class UserCreate(BaseModel):
    email: str
    password_hash: str
    avatar_url: Optional[str] = None
    role: str = "user"

class UserUpdate(BaseModel):
    email: str
    password_hash: str
    avatar_url: Optional[str] = None
    role: str

class UserPatch(BaseModel):
    email: Optional[str] = None
    password_hash: Optional[str] = None
    avatar_url: Optional[str] = None
    role: Optional[str] = None

class PresentationCreate(BaseModel):
    title: str
    owner_id: int

class PresentationUpdate(BaseModel):
    title: str

class QuestionCreate(BaseModel):
    type_code: str
    text: str
    media_url: Optional[str] = None
    order_index: int = 0
    settings: Optional[dict] = {}

class QuestionUpdate(BaseModel):
    type_code: str
    text: str
    media_url: Optional[str] = None
    order_index: int
    settings: Optional[dict] = {}

class OptionCreate(BaseModel):
    text: str
    is_correct: bool = False
    order_index: int = 0

class OptionUpdate(BaseModel):
    text: str
    is_correct: bool
    order_index: int

class LiveSessionCreate(BaseModel):
    access_code: str

class LiveSessionUpdate(BaseModel):
    status: str
    current_question_id: Optional[int] = None

class LiveSessionPatch(BaseModel):
    status: Optional[str] = None
    current_question_id: Optional[int] = None

class ParticipantCreate(BaseModel):
    nickname: str

class VoteCreate(BaseModel):
    participant_id: int
    question_id: int
    option_id: Optional[int] = None
    text_answer: Optional[str] = None

class QnAMessageCreate(BaseModel):
    text: str
    participant_id: int

class QnAMessageUpdate(BaseModel):
    is_answered: bool
    is_hidden: bool

class UpvoteCreate(BaseModel):
    participant_id: int