from pydantic import BaseModel


class AIChatRequest(BaseModel):
    prompt: str