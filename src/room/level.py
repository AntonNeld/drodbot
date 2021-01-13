from typing import Dict, Tuple

from pydantic import BaseModel

from .room import Room


class Level(BaseModel):
    """A representation of a level.

    Parameters
    ----------
    rooms
        The rooms, indexed by coordinates. The coordinates do not
        necessarily correspond to the in-game coordinates.
    """

    rooms: Dict[Tuple[int, int], Room] = {}

    # Override BaseModel.__init__(), to convert any string keys in 'rooms'
    # to tuples. This is needed to deserialize a JSON level.
    def __init__(self, **kwargs):
        if "rooms" in kwargs:
            new_rooms = {}
            for key, value in kwargs["rooms"].items():
                if isinstance(key, str):
                    new_key = tuple(
                        [int(coord) for coord in key.strip("()").split(",")]
                    )
                    new_rooms[new_key] = value
                else:
                    new_rooms[key] = value
            kwargs["rooms"] = new_rooms
        super().__init__(**kwargs)

    # Override BaseModel.dict(), to convert the keys in 'rooms' to strings.
    # This is needed to serialize it as JSON.
    def dict(self, **kwargs):
        as_dict = super().dict(**kwargs)
        new_rooms = {}
        for key, value in as_dict["rooms"].items():
            new_rooms[str(key)] = value
        as_dict["rooms"] = new_rooms
        return as_dict
