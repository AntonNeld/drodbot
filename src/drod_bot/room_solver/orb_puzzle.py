from collections import namedtuple

from .pathfinding import find_path
from room_simulator import ElementType, Direction
from room import Element, OrbEffectType
from search import a_star_graph, NoSolutionError

_State = namedtuple("_State", "position door_state")


class _OrbPuzzleProblem:
    def __init__(self, start, goals, room):
        self.start_position = start
        self.goals = goals
        self.room = room.copy(deep=True)
        self.orbs = self.room.find_coordinates(ElementType.ORB)
        self.door_coords_to_index = {}
        self.door_index_to_coords = []
        self.initial_door_state = []
        for i, coords in enumerate(self.room.find_coordinates(ElementType.YELLOW_DOOR)):
            self.initial_door_state.append(True)
            self.door_coords_to_index[coords] = i
            self.door_index_to_coords.append(coords)
        closed_door_amount = len(self.initial_door_state)
        for i, coords in enumerate(
            self.room.find_coordinates(ElementType.YELLOW_DOOR_OPEN)
        ):
            self.initial_door_state.append(False)
            self.door_coords_to_index[coords] = closed_door_amount + i
            self.door_index_to_coords.append(coords)
        self.expanded_orb_effects = {}
        for orb_coords in self.orbs:
            self.expanded_orb_effects[orb_coords] = []
            for effect, position in self.room.tile_at(orb_coords).item.orb_effects:
                door_tiles = set([position])
                edge = [position]
                while edge:
                    (x, y) = edge.pop()
                    for new_pos in [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]:
                        if (
                            new_pos not in door_tiles
                            and new_pos not in edge
                            and (
                                self.room.tile_at(new_pos).room_piece.element_type
                                == ElementType.YELLOW_DOOR
                                or self.room.tile_at(new_pos).room_piece.element_type
                                == ElementType.YELLOW_DOOR_OPEN
                            )
                        ):
                            door_tiles.add(new_pos)
                            edge.append(new_pos)
                self.expanded_orb_effects[orb_coords].extend(
                    [(effect, pos) for pos in door_tiles]
                )

    def initial_state(self):
        return _State(
            position=self.start_position, door_state=tuple(self.initial_door_state)
        )

    def actions(self, state):
        actions = []
        # Set the door state in the room
        for i, coords in enumerate(self.door_index_to_coords):
            if state.door_state[i]:
                self.room.tile_at(coords).room_piece = Element(
                    element_type=ElementType.YELLOW_DOOR
                )
            else:
                self.room.tile_at(coords).room_piece = Element(
                    element_type=ElementType.YELLOW_DOOR_OPEN
                )
        # See which goals are reachable
        for coords in self.goals:
            try:
                # Make up a direction for now
                cost = len(find_path(state.position, Direction.SE, [coords], self.room))
                actions.append((coords, cost))
            except NoSolutionError:
                pass
        # See which orbs are reachable
        for coords in self.orbs:
            try:
                # Make up a direction for now
                cost = len(
                    find_path(
                        state.position,
                        Direction.SE,
                        [coords],
                        self.room,
                        sword_at_goal=True,
                    )
                )
                actions.append((coords, cost))
            except NoSolutionError:
                pass
        return actions

    def result(self, state, action):
        destination, _ = action
        door_state = list(state.door_state)
        if destination in self.expanded_orb_effects:
            for effect, coords in self.expanded_orb_effects[destination]:
                index = self.door_coords_to_index[coords]
                if effect == OrbEffectType.OPEN:
                    door_state[index] = False
                elif effect == OrbEffectType.CLOSE:
                    door_state[index] = True
                else:  # Toggle
                    door_state[index] = not door_state[index]
        return _State(position=destination, door_state=tuple(door_state))

    def goal_test(self, state):
        return state.position in self.goals

    def step_cost(self, state, action, result):
        _, cost = action
        return cost


def _get_heuristic():
    def heuristic(state):
        # TODO: Some good heuristic?
        return 0

    return heuristic


def find_path_with_orbs(start, start_direction, goals, room, sword_at_goal=False):
    """Find a path from a position to the nearest goal position, with orbs and doors.

    Can't handle orbs that are reachable from multiple areas.

    Parameters
    ----------
    start
        The starting position given as a tuple (x, y).
    start_direction
        The starting direction.
    goals
        An iterable of goal positions, as tuples (x, y).
    room
        The room.
    sword_at_goal
        Whether the player's sword should be in the goal tiles rather than
        the player itself.

    Returns
    -------
    list of Action
        A sequence of actions to reach a goal position.
    """
    problem = _OrbPuzzleProblem(start, goals, room)
    solution = a_star_graph(problem, _get_heuristic())

    # Initialize the pathfinding room with starting position and direction
    pathfinding_room = room.copy(deep=True)
    player_position, _ = pathfinding_room.find_player()
    pathfinding_room.tile_at(player_position).monster = Element()
    pathfinding_room.tile_at(start).monster = Element(
        element_type=ElementType.BEETHRO, direction=start_direction
    )
    # Find the actual paths between the positions
    all_actions = []
    for coords, _ in solution:
        player_position, player_direction = pathfinding_room.find_player()
        if coords in goals:
            actions = find_path(
                player_position, player_direction, [coords], pathfinding_room
            )
        else:
            actions = find_path(
                player_position,
                player_direction,
                [coords],
                pathfinding_room,
                sword_at_goal=True,
            )
        all_actions.extend(actions)
        pathfinding_room.do_actions(actions, in_place=True)
    return all_actions
