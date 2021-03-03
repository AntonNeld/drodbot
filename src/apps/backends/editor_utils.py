from room_simulator import ElementType, Direction


async def place_sworded_element(interface, element, sword, x, y):
    """Place sworded elements to include all directions.

    Parameters
    ----------
    interface
        The editor interface.
    element
        The element to place.
    sword
        The sword belonging to the element.
    x
        X coordinate of the upper left corner of the pattern.
    y
        Y coordinate of the upper left corner of the pattern.

    Returns
    -------
    A list of tuples (element, direction, x, y, style) of placed elements.
    This includes the swords.
    """
    elements = [
        (element, Direction.N, x + 0, y + 1),
        (sword, Direction.N, x + 0, y + 0),
        (element, Direction.NE, x + 0, y + 2),
        (sword, Direction.NE, x + 1, y + 1),
        (element, Direction.E, x + 1, y + 0),
        (sword, Direction.E, x + 2, y + 0),
        (element, Direction.SE, x + 3, y + 0),
        (sword, Direction.SE, x + 4, y + 1),
        (element, Direction.S, x + 5, y + 1),
        (sword, Direction.S, x + 5, y + 2),
        (element, Direction.SW, x + 2, y + 1),
        (sword, Direction.SW, x + 1, y + 2),
        (element, Direction.W, x + 5, y + 0),
        (sword, Direction.W, x + 4, y + 0),
        (element, Direction.NW, x + 4, y + 2),
        (sword, Direction.NW, x + 3, y + 1),
    ]
    for (element, direction, element_x, element_y) in elements:
        if element != sword:
            await interface.place_element(element, direction, (element_x, element_y))
    return [(*e, None) for e in elements]


async def place_fully_directional_elements(interface, element, x, y, one_line=False):
    """Place directional elements to include all directions.

    This function is for fully directional elements, i.e. those
    that can face in 8 directions.

    Parameters
    ----------
    interface
        The editor interface.
    element
        The element to place.
    x
        X coordinate of the upper left corner of the pattern.
    y
        Y coordinate of the upper left corner of the pattern.
    one_line
        Whether to place the elements on one line instead of in a 4x2
        pattern.

    Returns
    -------
    A list of tuples (element, direction, x, y, style) of placed elements.
    """
    elements = [
        (element, Direction.N, x + 0, y + 0),
        (element, Direction.NE, x + 1, y + 0),
        (element, Direction.E, x + 2, y + 0),
        (element, Direction.SE, x + 3, y + 0),
    ]
    if one_line:
        elements.extend(
            [
                (element, Direction.S, x + 4, y + 0),
                (element, Direction.SW, x + 5, y + 0),
                (element, Direction.W, x + 6, y + 0),
                (element, Direction.NW, x + 7, y + 0),
            ]
        )
    else:
        elements.extend(
            [
                (element, Direction.S, x + 0, y + 1),
                (element, Direction.SW, x + 1, y + 1),
                (element, Direction.W, x + 2, y + 1),
                (element, Direction.NW, x + 3, y + 1),
            ]
        )
    for (element, direction, element_x, element_y) in elements:
        await interface.place_element(element, direction, (element_x, element_y))
    return [(*e, None) for e in elements]


async def place_nondirectional_edges_elements(interface, element, x, y, style=None):
    """Place nondirectional elements with edges to include many cases.

    Parameters
    ----------
    interface
        The editor interface.
    element
        The element to place.
    x
        X coordinate of the upper left corner of the pattern.
    y
        Y coordinate of the upper left corner of the pattern.
    style
        The style of the element.

    Returns
    -------
    A list of tuples (element, direction, x, y, style) of placed elements.
    Not all placed elements are included, to avoid duplicate images.
    """
    returned_coords = [
        # Little compact square
        (x + 0, y + 1),
        (x + 1, y + 1),
        (x + 2, y + 1),
        (x + 0, y + 2),
        (x + 1, y + 2),
        (x + 2, y + 2),
        (x + 0, y + 3),
        (x + 1, y + 3),
        (x + 2, y + 3),
        # Big holey square
        (x + 4, y + 0),
        (x + 4, y + 1),
        (x + 4, y + 2),
        (x + 5, y + 0),
        (x + 6, y + 0),
        (x + 6, y + 2),
        (x + 6, y + 4),
        (x + 8, y + 0),
        (x + 8, y + 2),
    ]
    not_returned_coords = [
        (x + 4, y + 3),
        (x + 4, y + 4),
        (x + 5, y + 2),
        (x + 5, y + 4),
        (x + 6, y + 1),
        (x + 6, y + 3),
        (x + 7, y + 0),
        (x + 7, y + 2),
        (x + 7, y + 4),
        (x + 8, y + 1),
        (x + 8, y + 3),
        (x + 8, y + 4),
    ]
    for (element_x, element_y) in returned_coords + not_returned_coords:
        await interface.place_element(
            element, Direction.NONE, (element_x, element_y), style=style
        )
    return [
        (element, Direction.NONE, element_x, element_y, style)
        for element_x, element_y in returned_coords
    ]


async def place_sized_obstacles(interface, style, x, y, sizes):
    """Place obstacles of various sizes.

    Parameters
    ----------
    interface
        The editor interface.
    style
        The style of the obstacle to place.
    x
        X coordinate of the leftmost obstacle.
    y
        Y coordinate of the leftmost obstacle.
    sizes
        List of sizes of obstacles.

    Returns
    -------
    A list of tuples (element, direction, x, y, style) of placed elements.
    """
    return_elements = []
    current_x = x
    for size in sizes:
        await interface.place_element(
            ElementType.OBSTACLE,
            Direction.NONE,
            (current_x, y),
            (current_x + size - 1, y + size - 1) if size != 1 else None,
            style=style,
        )
        for placed_x in range(current_x, current_x + size):
            for placed_y in range(y, y + size):
                return_elements.append(
                    (
                        ElementType.OBSTACLE,
                        Direction.NONE,
                        placed_x,
                        placed_y,
                        style,
                    )
                )
        current_x = current_x + size + 1
    return return_elements


async def place_rectangle(
    interface, element, x, y, width, height, include_all_sides=True, style=None
):
    """Place a rectangle of an element.

    Parameters
    ----------
    interface
        The editor interface.
    x
        X coordinate of the upper left corner.
    y
        Y coordinate of the upper left corner.
    width
        Width of the rectangle.
    height
        Height of the rectangle.
    include_all_sides
        If False, skip returning the left, right and lower sides. Use this
        when placing walls and you are only interested in the insides.
    style
        The style of element to place.

    Returns
    -------
    A list of tuples (element, direction, x, y, style) of placed elements.
    Some may be omitted, if `include_all_sides` is false.
    """
    await interface.place_element(
        element, Direction.NONE, (x, y), (x + width - 1, y + height - 1), style=style
    )
    return_elements = []
    if include_all_sides:
        x_range = range(x, x + width)
        y_range = range(y, y + height)
    else:
        x_range = range(x + 1, x + width - 1)
        y_range = range(y, y + height - 1)
    for placed_x in x_range:
        for placed_y in y_range:
            return_elements.append((element, Direction.NONE, placed_x, placed_y, style))
    return return_elements
