from pydantic import BaseModel, Field
from typing import List

from common import ROOM_HEIGHT_IN_TILES, ROOM_WIDTH_IN_TILES
from .element import (
    ElementType,
    Direction,
    OrbEffectType,
    UndirectionalElement,
    Orb,
    DirectionalElement,
    Beethro,
    element_from_apparent,
    element_to_apparent,
)
from .tile import Tile
from .apparent_tile import ApparentTile
from util import position_in_direction
import room_simulator


class Room(BaseModel):
    """A representation of a room.

    Parameters
    ----------
    tiles
        The room tiles as a list of lists containing Tile objects.
    """

    tiles: List[List[Tile]] = Field(
        default_factory=lambda: [
            [
                Tile(room_piece=UndirectionalElement(element_type=ElementType.FLOOR))
                for y in range(ROOM_HEIGHT_IN_TILES)
            ]
            for x in range(ROOM_WIDTH_IN_TILES)
        ]
    )

    def tile_at(self, position):
        """Return the tile at the given position.

        Parameters
        ----------
        position
            A tuple (x, y).

        Returns
        -------
        The tile at that position.
        """
        x, y = position
        return self.tiles[x][y]

    def find_coordinates(self, element):
        """Find the coordinates of all elements of a type.

        Parameters
        ----------
        element
            The element type to find the coordinates of.

        Returns
        -------
        The coordinates of all elements of that type, as a list of (x, y) tuples.
        """
        return [
            (x, y)
            for x, columns in enumerate(self.tiles)
            for y, tile in enumerate(columns)
            if element in tile.get_element_types()
        ]

    def find_player(self):
        """Find the coordinates of the player.

        Returns
        -------
        A tuple ((x, y), direction).
        """
        beethros = self.find_coordinates(ElementType.BEETHRO)
        if len(beethros) < 1:
            raise RuntimeError("Cannot find Beethro")
        if len(beethros) > 1:
            raise RuntimeError(f"Too many Beethros: {beethros}")
        position = beethros[0]
        direction = self.tile_at(position).monster.direction
        return position, direction

    def do_actions(self, actions, in_place=False):
        """Do multiple actions, and return a copy of the room after the actions.

        Parameters
        ----------
        actions
            The actions to perform.
        in_place
            Whether to modify the room in place. The room will still be
            returned. Use this if you will not use the old room and performance
            is critical.

        Returns
        -------
        A copy of the room after having performed the actions.
        """
        if in_place:
            room = self
        else:
            room = self.copy(deep=True)
        for action in actions:
            room._do_action_in_place(action)
        return room

    def do_action(self, action, in_place=False):
        """Do an action, and return a copy of the room after the action.

        The room after will match the result of performing an
        action in the actual game.

        Parameters
        ----------
        action
            The action to perform.
        in_place
            Whether to modify the room in place. The room will still be
            returned. Use this if you will not use the old room and performance
            is critical.

        Returns
        -------
        A copy of the room after having performed the action. If `in_place`
        is True, return the same room instance.
        """
        if in_place:
            room = self
        else:
            room = self.copy(deep=True)
        room._do_action_in_place(action)
        return room

    def _do_action_in_place(self, action):
        # Do nothing with the result for now
        room_after = room_simulator.simulate_action(
            self._to_simulator_room(), action.value
        )
        self._set_from_simulator_room(room_after)

        position, direction = self.find_player()
        sword_position = position_in_direction(position, direction)
        if (
            sword_position[0] >= 0
            and sword_position[0] < ROOM_WIDTH_IN_TILES
            and sword_position[1] >= 0
            and sword_position[1] < ROOM_HEIGHT_IN_TILES
        ):
            under_sword = self.tile_at(sword_position)
            if (
                under_sword.item is not None
                and under_sword.item.element_type == ElementType.ORB
            ):
                for effect, pos in under_sword.item.effects:
                    if self.tile_at(pos).room_piece is None:
                        raise RuntimeError(
                            f"Orb at {sword_position} tried to {effect} element "
                            f"at {pos}, but nothing is there"
                        )
                    if self.tile_at(pos).room_piece.element_type not in [
                        ElementType.YELLOW_DOOR,
                        ElementType.YELLOW_DOOR_OPEN,
                    ]:
                        raise RuntimeError(
                            f"Orb at {sword_position} tried to {effect} element "
                            f"at {pos}, but it is a "
                            f"{self.tile_at(pos).room_piece.element_type}"
                        )
                    if effect == OrbEffectType.OPEN:
                        self.tile_at(pos).room_piece = UndirectionalElement(
                            element_type=ElementType.YELLOW_DOOR_OPEN
                        )
                    elif effect == OrbEffectType.CLOSE:
                        self.tile_at(pos).room_piece = UndirectionalElement(
                            element_type=ElementType.YELLOW_DOOR
                        )
                    # Toggle
                    elif (
                        self.tile_at(pos).room_piece.element_type
                        == ElementType.YELLOW_DOOR
                    ):
                        self.tile_at(pos).room_piece = UndirectionalElement(
                            element_type=ElementType.YELLOW_DOOR_OPEN
                        )
                    else:
                        self.tile_at(pos).room_piece = UndirectionalElement(
                            element_type=ElementType.YELLOW_DOOR
                        )

    def _to_simulator_room(self):
        simulator_room = []
        for column in self.tiles:
            simulator_column = []
            for tile in column:
                simulator_tile = room_simulator.Tile()
                simulator_tile.room_piece = _to_simulator_element(tile.room_piece)
                simulator_tile.floor_control = _to_simulator_element(tile.floor_control)
                simulator_tile.checkpoint = _to_simulator_element(tile.checkpoint)
                simulator_tile.item = _to_simulator_element(tile.item)
                simulator_tile.monster = _to_simulator_element(tile.monster)
                simulator_column.append(simulator_tile)
            simulator_room.append(simulator_column)

        return simulator_room

    def _set_from_simulator_room(self, simulator_room):
        tiles = []
        for x, simulator_column in enumerate(simulator_room):
            column = []
            for y, simulator_tile in enumerate(simulator_column):
                room_piece = _from_simulator_element(simulator_tile.room_piece)
                floor_control = _from_simulator_element(simulator_tile.floor_control)
                checkpoint = _from_simulator_element(simulator_tile.checkpoint)
                item = _from_simulator_element(simulator_tile.item)
                if item is not None and item.element_type == ElementType.ORB:
                    item.effects = self.tiles[x][y].item.effects
                monster = _from_simulator_element(simulator_tile.monster)
                column.append(
                    Tile(
                        room_piece=room_piece,
                        floor_control=floor_control,
                        checkpoint=checkpoint,
                        item=item,
                        monster=monster,
                    )
                )
            tiles.append(column)
        self.tiles = tiles

    def to_apparent_tiles(self):
        """Create apparent tiles from a room.

        Returns
        -------
        A dict mapping coordinates to ApparentTile instances.
        """
        return {
            (x, y): ApparentTile(
                room_piece=element_to_apparent(tile.room_piece),
                floor_control=element_to_apparent(tile.floor_control),
                checkpoint=element_to_apparent(tile.checkpoint),
                item=element_to_apparent(tile.item),
                monster=element_to_apparent(tile.monster),
            )
            for x, columns in enumerate(self.tiles)
            for y, tile in enumerate(columns)
        }

    @staticmethod
    def from_apparent_tiles(apparent_tiles, orb_effects=None):
        """Create a room from apparent tiles.

        Not all information will be present in the beginning, only
        what can be seen without making any moves.

        Parameters
        ----------
        apparent_tiles
            A dict mapping coordinates to ApparentTile instances.
        orb_effects
            An optional dict mapping coordinates to (orb_effect, (x, y)),
            that gives the effects of orbs in the room.

        Returns
        -------
        A new room.
        """
        room = Room()
        for (x, y), tile in apparent_tiles.items():
            room.tiles[x][y] = Tile(
                room_piece=element_from_apparent(*tile.room_piece),
                floor_control=element_from_apparent(*tile.floor_control),
                checkpoint=element_from_apparent(*tile.checkpoint),
                item=element_from_apparent(*tile.item),
                monster=element_from_apparent(*tile.monster),
            )

        if orb_effects is not None:
            for position, effects in orb_effects.items():
                room.tile_at(position).item.effects = effects
        return room


def _to_simulator_element(element):
    """Creates a simulator element from an element.

    Parameters
    ----------
    element
        The element to convert.

    Returns
    -------
    A simulator element.
    """
    if element is None:
        return room_simulator.Element()
    if element.element_type == ElementType.WALL:
        return room_simulator.Element(element_type=room_simulator.ElementType.WALL)
    if element.element_type == ElementType.PIT:
        return room_simulator.Element(element_type=room_simulator.ElementType.PIT)
    if element.element_type == ElementType.MASTER_WALL:
        return room_simulator.Element(
            element_type=room_simulator.ElementType.MASTER_WALL
        )
    if element.element_type == ElementType.YELLOW_DOOR:
        return room_simulator.Element(
            element_type=room_simulator.ElementType.YELLOW_DOOR
        )
    if element.element_type == ElementType.YELLOW_DOOR_OPEN:
        return room_simulator.Element(
            element_type=room_simulator.ElementType.YELLOW_DOOR_OPEN
        )
    if element.element_type == ElementType.GREEN_DOOR:
        return room_simulator.Element(
            element_type=room_simulator.ElementType.GREEN_DOOR
        )
    if element.element_type == ElementType.GREEN_DOOR_OPEN:
        return room_simulator.Element(
            element_type=room_simulator.ElementType.GREEN_DOOR_OPEN
        )
    if element.element_type == ElementType.BLUE_DOOR:
        return room_simulator.Element(element_type=room_simulator.ElementType.BLUE_DOOR)
    if element.element_type == ElementType.BLUE_DOOR_OPEN:
        return room_simulator.Element(
            element_type=room_simulator.ElementType.BLUE_DOOR_OPEN
        )
    if element.element_type == ElementType.STAIRS:
        return room_simulator.Element(element_type=room_simulator.ElementType.STAIRS)
    if element.element_type == ElementType.CHECKPOINT:
        return room_simulator.Element(
            element_type=room_simulator.ElementType.CHECKPOINT
        )
    if element.element_type == ElementType.SCROLL:
        return room_simulator.Element(element_type=room_simulator.ElementType.SCROLL)
    if element.element_type == ElementType.OBSTACLE:
        return room_simulator.Element(element_type=room_simulator.ElementType.OBSTACLE)
    if element.element_type == ElementType.CONQUER_TOKEN:
        return room_simulator.Element(
            element_type=room_simulator.ElementType.CONQUER_TOKEN
        )
    if element.element_type == ElementType.FLOOR:
        return room_simulator.Element(element_type=room_simulator.ElementType.FLOOR)
    # TODO: orb effects
    if element.element_type == ElementType.ORB:
        return room_simulator.Element(element_type=room_simulator.ElementType.ORB)
    # Directional elements
    if element.direction == Direction.N:
        direction = room_simulator.Direction.N
    if element.direction == Direction.NE:
        direction = room_simulator.Direction.NE
    if element.direction == Direction.E:
        direction = room_simulator.Direction.E
    if element.direction == Direction.SE:
        direction = room_simulator.Direction.SE
    if element.direction == Direction.S:
        direction = room_simulator.Direction.S
    if element.direction == Direction.SW:
        direction = room_simulator.Direction.SW
    if element.direction == Direction.W:
        direction = room_simulator.Direction.W
    if element.direction == Direction.NW:
        direction = room_simulator.Direction.NW

    if element.element_type == ElementType.FORCE_ARROW:
        return room_simulator.Element(
            element_type=room_simulator.ElementType.FORCE_ARROW, direction=direction
        )
    if element.element_type == ElementType.BEETHRO:
        return room_simulator.Element(
            element_type=room_simulator.ElementType.BEETHRO, direction=direction
        )
    if element.element_type == ElementType.ROACH:
        return room_simulator.Element(
            element_type=room_simulator.ElementType.ROACH, direction=direction
        )


def _from_simulator_element(simulator_element):
    """Creates an element from a simulator element.

    Parameters
    ----------
    simulator_element
        The simulator melement to convert.

    Returns
    -------
    An element.
    """
    element_type = simulator_element.element_type
    element_direction = simulator_element.direction
    if element_type == room_simulator.ElementType.NOTHING:
        return None
    if element_type == room_simulator.ElementType.WALL:
        return UndirectionalElement(element_type=ElementType.WALL)
    if element_type == room_simulator.ElementType.PIT:
        return UndirectionalElement(element_type=ElementType.PIT)
    if element_type == room_simulator.ElementType.MASTER_WALL:
        return UndirectionalElement(element_type=ElementType.MASTER_WALL)
    if element_type == room_simulator.ElementType.YELLOW_DOOR:
        return UndirectionalElement(element_type=ElementType.YELLOW_DOOR)
    if element_type == room_simulator.ElementType.YELLOW_DOOR_OPEN:
        return UndirectionalElement(element_type=ElementType.YELLOW_DOOR_OPEN)
    if element_type == room_simulator.ElementType.GREEN_DOOR:
        return UndirectionalElement(element_type=ElementType.GREEN_DOOR)
    if element_type == room_simulator.ElementType.GREEN_DOOR_OPEN:
        return UndirectionalElement(element_type=ElementType.GREEN_DOOR_OPEN)
    if element_type == room_simulator.ElementType.BLUE_DOOR:
        return UndirectionalElement(element_type=ElementType.BLUE_DOOR)
    if element_type == room_simulator.ElementType.BLUE_DOOR_OPEN:
        return UndirectionalElement(element_type=ElementType.BLUE_DOOR_OPEN)
    if element_type == room_simulator.ElementType.STAIRS:
        return UndirectionalElement(element_type=ElementType.STAIRS)
    if element_type == room_simulator.ElementType.CHECKPOINT:
        return UndirectionalElement(element_type=ElementType.CHECKPOINT)
    if element_type == room_simulator.ElementType.SCROLL:
        return UndirectionalElement(element_type=ElementType.SCROLL)
    if element_type == room_simulator.ElementType.OBSTACLE:
        return UndirectionalElement(element_type=ElementType.OBSTACLE)
    if element_type == room_simulator.ElementType.CONQUER_TOKEN:
        return UndirectionalElement(element_type=ElementType.CONQUER_TOKEN)
    if element_type == room_simulator.ElementType.FLOOR:
        return UndirectionalElement(element_type=ElementType.FLOOR)
    # TODO: orb effects
    if element_type == room_simulator.ElementType.ORB:
        return Orb()
    # Directional elements
    if element_direction == room_simulator.Direction.N:
        direction = Direction.N
    if element_direction == room_simulator.Direction.NE:
        direction = Direction.NE
    if element_direction == room_simulator.Direction.E:
        direction = Direction.E
    if element_direction == room_simulator.Direction.SE:
        direction = Direction.SE
    if element_direction == room_simulator.Direction.S:
        direction = Direction.S
    if element_direction == room_simulator.Direction.SW:
        direction = Direction.SW
    if element_direction == room_simulator.Direction.W:
        direction = Direction.W
    if element_direction == room_simulator.Direction.NW:
        direction = Direction.NW

    if element_type == room_simulator.ElementType.FORCE_ARROW:
        return DirectionalElement(
            element_type=ElementType.FORCE_ARROW, direction=direction
        )
    if element_type == room_simulator.ElementType.BEETHRO:
        return Beethro(direction=direction)
    if element_type == room_simulator.ElementType.ROACH:
        return DirectionalElement(element_type=ElementType.ROACH, direction=direction)
