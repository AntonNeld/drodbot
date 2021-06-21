from typing import Optional, Tuple, List

from pydantic import BaseModel, Field, validator

from .level import Level
from .dict_conversion import room_from_dict, room_to_dict
from room_simulator import Room, Action


class DrodBotState(BaseModel):
    """The state of DRODbot.

    Parameters
    ----------
    level
        The level it's playing, with the rooms as they are when entering them.
    current_room
        The current room being played, as it is now.
    current_room_position.
        The position in the level of the current room.
    plan
        The current plan to execute.
    """

    level: Level = Field(default_factory=lambda: Level())
    current_room: Optional[Room]
    current_room_position: Tuple[int, int] = (0, 0)
    room_backlog: List[
        Tuple[
            # (room coord, tile coord)
            Tuple[int, int],
            Tuple[int, int],
        ]
    ] = []
    plan: List[Action] = []

    class Config:
        json_encoders = {Room: room_to_dict, Action: lambda a: a.name}
        arbitrary_types_allowed = True

    @validator("plan", pre=True)
    def parse_plan(cls, v):
        return [
            action if isinstance(action, Action) else getattr(Action, action)
            for action in v
        ]

    @validator("current_room", pre=True)
    def parse_room(cls, v):
        return v if isinstance(v, Room) else room_from_dict(v)
