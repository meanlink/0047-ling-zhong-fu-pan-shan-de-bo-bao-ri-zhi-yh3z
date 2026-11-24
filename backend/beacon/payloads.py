from datetime import datetime
from typing import Literal
from pydantic import BaseModel,Field,model_validator

Key=Field(pattern=r"^[A-Z0-9-]{3,24}$")

class Pair(BaseModel):
    code:str=Key
    clock:str=Key
    source_at:datetime
    observed_at:datetime
    import_note:str=Field(min_length=3,max_length=255)

    @model_validator(mode="after")
    def zones(self):
        if any(d.utcoffset() is None for d in (self.source_at,self.observed_at)):
            raise ValueError("必须提供时区偏移")
        return self

class Note(BaseModel):
    label:Literal["unstable","human"]
    note:str=Field(min_length=5,max_length=240)
