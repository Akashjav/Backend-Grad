from pydantic import BaseModel
from typing import Optional


class AlumniPayoutCreate(BaseModel):
    alumni_id: str
    payment_method: Optional[str] = "manual"
    transaction_id: Optional[str] = None