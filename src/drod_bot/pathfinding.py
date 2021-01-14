from common import Action
from room import Element
from .search import a_star_graph


class _PathfindingProblem:
    def __init__(self, start, goals, obstacles):
        self.start = start
        self.goals = goals
        self.obstacles = obstacles

    def initial_state(self):
        return self.start

    def actions(self, state):
        actions = []
        x = state[0]
        y = state[1]
        if (x, y - 1) not in self.obstacles:
            actions.append(Action.N)
        if (x + 1, y - 1) not in self.obstacles:
            actions.append(Action.NE)
        if (x + 1, y) not in self.obstacles:
            actions.append(Action.E)
        if (x + 1, y + 1) not in self.obstacles:
            actions.append(Action.SE)
        if (x, y + 1) not in self.obstacles:
            actions.append(Action.S)
        if (x - 1, y + 1) not in self.obstacles:
            actions.append(Action.SW)
        if (x - 1, y) not in self.obstacles:
            actions.append(Action.W)
        if (x - 1, y - 1) not in self.obstacles:
            actions.append(Action.NW)
        return actions

    def result(self, state, action):
        x = state[0]
        y = state[1]
        if action == Action.N:
            return (x, y - 1)
        elif action == Action.NE:
            return (x + 1, y - 1)
        elif action == Action.E:
            return (x + 1, y)
        elif action == Action.SE:
            return (x + 1, y + 1)
        elif action == Action.S:
            return (x, y + 1)
        elif action == Action.SW:
            return (x - 1, y + 1)
        elif action == Action.W:
            return (x - 1, y)
        elif action == Action.NW:
            return (x - 1, y - 1)
        raise RuntimeError(f"Uknown action {action}")

    def goal_test(self, state):
        return state in self.goals

    def step_cost(self, state, action, result):
        return 1


def _get_heuristic(goals):
    def heuristic(state):
        distances = [
            max(abs(goal[0] - state[0]), abs(goal[1] - state[1])) for goal in goals
        ]
        if distances:
            return min(distances)
        return 0

    return heuristic


def find_path(start, goals, room):
    """Find a path from a position to the nearest goal position.

    Parameters
    ----------
    start
        The starting position given as a tuple (x, y).
    goals
        An iterable of goal positions, as tuples (x, y).
    room
        Entities in the room, as a dict of positions to lists of entities.

    Returns
    -------
    list of Action
        The shortest sequence of actions to reach a goal position.
    """
    obstacles = set()
    for element in [
        Element.WALL,
        Element.MASTER_WALL,
        Element.OBSTACLE,
        Element.YELLOW_DOOR,
        Element.BLUE_DOOR,
        Element.GREEN_DOOR,
        Element.ORB,
        Element.PIT,
    ]:
        obstacles.update(room.find_coordinates(element))
    problem = _PathfindingProblem(start, goals, obstacles)
    solution = a_star_graph(problem, _get_heuristic(goals))
    return solution


def get_position_after(actions, position_before):
    """Get the new position after the given actions.

    This function assumes that the path is not blocked
    and never goes outside the room.

    Parameters
    ----------
    actions
        A list of actions.
    position_before
        The starting position as an (x, y) tuple.

    Returns
    -------
    The resulting position as an (x, y) tuple.
    """
    x = position_before[0]
    y = position_before[1]
    x += actions.count(Action.NE) + actions.count(Action.E) + actions.count(Action.SE)
    x -= actions.count(Action.NW) + actions.count(Action.W) + actions.count(Action.SW)
    y += actions.count(Action.SE) + actions.count(Action.S) + actions.count(Action.SW)
    y -= actions.count(Action.NE) + actions.count(Action.N) + actions.count(Action.NW)
    return (x, y)
