from typing import Annotated, Optional


from pydantic import BaseModel, BeforeValidator, Field

PyObjectId = Annotated[str, BeforeValidator(str)]


class MongoBaseModel(BaseModel):
    id: Optional[PyObjectId] = Field(
        alias="_id", serialization_alias="id", default=None
    )
