from collections import namedtuple

from common import Action, ROOM_HEIGHT_IN_TILES, ROOM_WIDTH_IN_TILES
from room import ElementType, Direction
from search import a_star_graph, NoSolutionError
from util import direction_after, position_in_direction, inside_room

_State = namedtuple("_State", "position direction")


class _PathfindingProblem:
    def __init__(self, start, start_direction, goals, obstacles, sword_at_goal):
        self.start = start
        self.start_direction = start_direction
        self.goals = goals
        self.obstacles = obstacles
        self.sword_at_goal = sword_at_goal

    def initial_state(self):
        return _State(position=self.start, direction=self.start_direction)

    def actions(self, state):
        actions = [Action.CW, Action.CCW]
        x, y = state.position
        if (x, y - 1) not in self.obstacles and y > 0:
            actions.append(Action.N)
        if (
            (x + 1, y - 1) not in self.obstacles
            and y > 0
            and x < ROOM_WIDTH_IN_TILES - 1
        ):
            actions.append(Action.NE)
        if (x + 1, y) not in self.obstacles and x < ROOM_WIDTH_IN_TILES - 1:
            actions.append(Action.E)
        if (
            (x + 1, y + 1) not in self.obstacles
            and y < ROOM_HEIGHT_IN_TILES - 1
            and x < ROOM_WIDTH_IN_TILES - 1
        ):
            actions.append(Action.SE)
        if (x, y + 1) not in self.obstacles and y < ROOM_HEIGHT_IN_TILES - 1:
            actions.append(Action.S)
        if (
            (x - 1, y + 1) not in self.obstacles
            and y < ROOM_HEIGHT_IN_TILES - 1
            and x > 0
        ):
            actions.append(Action.SW)
        if (x - 1, y) not in self.obstacles and x > 0:
            actions.append(Action.W)
        if (x - 1, y - 1) not in self.obstacles and y > 0 and x > 0:
            actions.append(Action.NW)
        return actions

    def result(self, state, action):
        x, y = state.position
        direction = state.direction
        if action == Action.CW:
            return _State(
                position=(x, y), direction=direction_after([Action.CW], direction)
            )
        elif action == Action.CCW:
            return _State(
                position=(x, y), direction=direction_after([Action.CCW], direction)
            )
        else:
            return _State(
                position=position_in_direction((x, y), action), direction=direction
            )

    def goal_test(self, state):
        if self.sword_at_goal:
            return position_in_direction(state.position, state.direction) in self.goals
        else:
            return state.position in self.goals

    def step_cost(self, state, action, result):
        return 1


def _get_heuristic(goals):
    def heuristic(state):
        distances = [
            max(abs(goal[0] - state.position[0]), abs(goal[1] - state.position[1]))
            for goal in goals
        ]
        if distances:
            return min(distances)
        return 0

    return heuristic


def find_path(start, start_direction, goals, room, sword_at_goal=False):
    """Find a path from a position to the nearest goal position.

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
        The shortest sequence of actions to reach a goal position.
    """
    obstacles = set()
    for element in [
        ElementType.WALL,
        ElementType.MASTER_WALL,
        ElementType.OBSTACLE,
        ElementType.YELLOW_DOOR,
        ElementType.BLUE_DOOR,
        ElementType.GREEN_DOOR,
        ElementType.ORB,
        ElementType.PIT,
    ]:
        obstacles.update(room.find_coordinates(element))
    if not _is_reachable(start, goals, obstacles):
        raise NoSolutionError(0, precheck_failed=True)
    problem = _PathfindingProblem(
        start, start_direction, goals, obstacles, sword_at_goal=sword_at_goal
    )
    solution = a_star_graph(problem, _get_heuristic(goals))
    return solution


def _is_reachable(start, goals, obstacles):
    """Check whether any of the goals is reachable at all.

    A quick sanity check to see whether it's worth it to
    search for a solution.

    Parameters
    ----------
    start
        Starting position (x, y).
    goals
        Iterable of goal positions (x, y).
    obstacles
        Set of obstacles (x, y).

    Returns
    -------
    Whether any of the goals has the potential to be reachable.
    Even if this function returns True, there is no guarantee a
    solution exists.
    """
    # Simultaneously fill regions centered on the goals and player,
    # and see if they touch.
    goal_edge = set(goals)
    goal_filled = set()
    player_edge = set([start])
    player_filled = set()
    while goal_edge and player_edge:
        for edge, filled in [(goal_edge, goal_filled), (player_edge, player_filled)]:
            if goal_edge & player_edge:
                return True
            new_edge = set()
            for coords in edge:
                for new_coords in [
                    position_in_direction(coords, direction)
                    for direction in [
                        Direction.N,
                        Direction.NE,
                        Direction.E,
                        Direction.SE,
                        Direction.S,
                        Direction.SW,
                        Direction.W,
                        Direction.NW,
                    ]
                ]:
                    if new_coords not in obstacles | filled | edge and inside_room(
                        new_coords
                    ):
                        new_edge.add(new_coords)
            filled.update(goal_edge)
            edge.clear()
            edge.update(new_edge)
    return False
