from sortedcontainers import SortedList


class NoSolutionError(Exception):
    """An error indicating that no solution was found.

    Attributes
    ----------
    iterations
        The number of iterations the search went through.
    iteration_limited
        Whether the search failed because the maximum number
        of iterations was reached.
    """

    def __init__(self, iterations, depth_limited=False, iteration_limited=False):
        self.iterations = iterations
        self.iteration_limited = iteration_limited


class _Node:
    def __init__(self, state, path_cost, parent=None, action=None):
        self.state = state
        self.path_cost = path_cost
        self.parent = parent
        self.action = action

    def get_child(self, problem, action):
        state = problem.result(self.state, action)
        path_cost = self.path_cost + problem.step_cost(self.state, action, state)
        return _Node(state, path_cost, parent=self, action=action)

    def solution(self):
        if self.parent is None:
            return []
        return self.parent.solution() + [self.action]


def a_star_graph(problem, heuristic, iteration_limit=10000):
    """Do an A* search to find the solution to a given problem.

    Parameters
    ----------
    problem
        The problem to solve. It must have the following methods:
        - initial_state(), which returns the initial state.
        - actions(state), which returns the possible actions in `state`.
        - result(state, action), which returns the resulting state after
            performing `action` in `state`.
        - goal_test(state), which checks whether `state` is a goal state.
        - step_cost(state, action, result), which returns the step cost for
            the given state transition.
        States should be hashable, but can otherwise have any type. Actions
        can have any type.
    heuristic
        A heuristic function that takes a state and returns an estimate of
        the path cost from that state to a goal state. To get an optimal
        solution, it should never overestimate the path cost.
    iteration_limit
        A limit on the number of iterations before raising a NoSolutionError.
        This is to prevent freezing if the problem is too difficult.

    Returns
    -------
    list of action
        The sequence of actions that solves the problem.

    Raises
    ------
    NoSolutionError
        Raised if there is no solution, or if the max number of iterations
        was reached.
    """
    starting_node = _Node(problem.initial_state(), 0)
    if problem.goal_test(starting_node.state):
        return starting_node.solution()
    frontier = SortedList(
        [starting_node], key=lambda n: -(n.path_cost + heuristic(n.state))
    )
    explored = set()
    iterations = 0
    while frontier:
        node = frontier.pop()
        if problem.goal_test(node.state):
            return node.solution()
        explored.add(node.state)
        for action in problem.actions(node.state):
            child = node.get_child(problem, action)
            child_in_frontier = child.state in [n.state for n in frontier]
            if child.state not in explored and not child_in_frontier:
                frontier.add(child)
            elif child_in_frontier:
                index = [n.state for n in frontier].index(child.state)
                other_node = frontier[index]
                if child.path_cost < other_node.path_cost:
                    frontier.remove(other_node)
                    frontier.add(child)

        iterations += 1
        if iterations > iteration_limit:
            raise NoSolutionError(iterations=iterations, iteration_limited=True)
    raise NoSolutionError(iterations=iterations)
