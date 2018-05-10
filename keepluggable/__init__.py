"""**keepluggable** contains reusable code that stores files and images."""

from pydantic import BaseModel, conint, constr

AtLeastOneChar: constr = constr(min_length=1, strip_whitespace=True)
ZeroOrMore: conint = conint(gt=-1)


class Pydantic(BaseModel):
    """Base class for our validation models."""

    class Config:
        """Controls the behaviour of pydantic."""

        anystr_strip_whitespace = True
        min_anystr_length = 1
