from typing import List, Tuple

from pydantic import BaseModel, validator

from room_simulator import ElementType, Direction, OrbEffect


class Element(BaseModel):
    """A game element."""

    element_type: ElementType = ElementType.NOTHING
    direction: Direction = Direction.NONE
    orb_effects: List[Tuple[int, int, OrbEffect]] = []

    @validator("element_type", pre=True)
    def element_type_name_to_enum(cls, v):
        return v if isinstance(v, ElementType) else getattr(ElementType, v)

    @validator("direction", pre=True)
    def direction_name_to_enum(cls, v):
        return v if isinstance(v, Direction) else getattr(Direction, v)

    @validator("orb_effects", pre=True)
    def orb_effect_name_to_enum(cls, v):
        return [
            (x, y, effect)
            if isinstance(effect, OrbEffect)
            else (x, y, getattr(OrbEffect, effect))
            for (x, y, effect) in v
        ]

    class Config:
        arbitrary_types_allowed = True
