# Add Pydantic schemas here that you'll use in your routes / endpoints
# Pydantic schemas are used to validate data that you receive, or to make sure that whatever data
# you send back to the client follows a certain structure
from typing import Optional

from pydantic import BaseModel


# Dörrvakt för nya användare
class UserCreate(BaseModel):
    email: str
    password_hash: str
    avatar_url: Optional[str] = None

# Dörrvakt för nya presentationer
class PresentationCreate(BaseModel):
    title: str
    owner_id: int