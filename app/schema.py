from pydantic import BaseModel

class Postcreat (BaseModel):
    titel:str
    content:str

class PostResponse(BaseModel):
    title: str
    content: str
