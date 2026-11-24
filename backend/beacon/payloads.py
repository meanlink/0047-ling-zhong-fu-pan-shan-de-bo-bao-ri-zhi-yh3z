from datetime import datetime
from typing import Literal, Optional, Union
from pydantic import BaseModel,ConfigDict,Field,model_validator

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


class Decision(BaseModel):
    # 接受参考实现可能使用的各种来源/借用字段名，未知字段也保留给提取器。
    model_config = ConfigDict(extra="allow")
    borrow: Optional[Union[bool,str]] = None
    auto_borrow: Optional[bool] = None
    source: Optional[str] = None
    borrowed_from: Optional[str] = None
    borrow_from: Optional[str] = None
    borrow_source: Optional[str] = None
    source_tour: Optional[str] = None
    source_code: Optional[str] = None
    from_tour: Optional[str] = None
    origin_tour: Optional[str] = None
    origin: Optional[str] = None
    night_adjust_ms: Optional[float] = None
    adjust_ms: Optional[float] = None


class VoidBody(BaseModel):
    model_config = ConfigDict(extra="allow")
    reason: Optional[str] = Field(default=None, max_length=240)
    note: Optional[str] = Field(default=None, max_length=240)
    idempotency_key: Optional[str] = Field(default=None, max_length=120)
