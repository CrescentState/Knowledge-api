
from pydantic import BaseModel, ConfigDict


class CoreModel(BaseModel):
    """Base model for all schemas to ensure consistency."""

    model_config = ConfigDict(
        from_attributes=True,  # Allows compatibility with ORMs
        validate_assignment=True,
        arbitrary_types_allowed=True,
        str_strip_whitespace=True,
    )
