from typing import List, Tuple, Literal

from pydantic import BaseModel

from .pathfinding import find_path


class ReachTileObjective(BaseModel):
    """Try to reach one of a set of tiles.

    Parameters
    ----------
    goal_tiles
        If Beethro is in any of these coordinates, the objective
        is reached.
    """

    objective_type: Literal["reach_tile"] = "reach_tile"
    goal_tiles: List[Tuple[int, int]]


class StrikeTileObjective(BaseModel):
    """Try to strike one of a set of tiles.

    Parameters
    ----------
    goal_tiles
        If Beethro's sword is in any of these coordinates,
        the objective is reached.
    """

    objective_type: Literal["strike_tile"] = "strike_tile"
    goal_tiles: List[Tuple[int, int]]


def solve_room(room, objective):
    """Find a sequence of actions to solve a room.

    Parameters
    ----------
    room
        The room to solve
    objective
        The objective to reach.
    """
    if objective.objective_type == "reach_tile":
        player_position = room.find_player()
        direction = room.tiles[player_position].monster.direction
        goal_positions = objective.goal_tiles
        actions = find_path(player_position, direction, goal_positions, room)
        return actions
    if objective.objective_type == "strike_tile":
        player_position = room.find_player()
        direction = room.tiles[player_position].monster.direction
        goal_positions = objective.goal_tiles
        actions = find_path(
            player_position, direction, goal_positions, room, sword_at_goal=True
        )
        return actions
    else:
        raise RuntimeError(f"Unknown objective {objective.objective_type}")
