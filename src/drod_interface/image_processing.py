import numpy


def find_color(image, color):
    r = image[:, :, 0]
    g = image[:, :, 1]
    b = image[:, :, 2]
    return numpy.logical_and.reduce(
        [
            r == color[0],
            g == color[1],
            b == color[2],
        ]
    )


def find_horizontal_lines(boolean_array, length):
    # Pad, to find lines that start or end at the edges
    int_array = numpy.pad(boolean_array.astype(int), (0, 1))
    # Coords of the first pixel in each line
    starts = numpy.argwhere(numpy.diff(int_array) == 1) + (0, 1)
    # Coords of the pixel after the last in each line
    ends = numpy.argwhere(numpy.diff(int_array) == -1) + (0, 1)
    lines = []
    for coords in starts:
        start_x = coords[1]
        start_y = coords[0]
        end_x = [e[1] for e in ends if e[0] == start_y]
        if start_x + length in end_x and not any(
            [x > start_x and x < start_x + length for x in end_x]
        ):
            # We have an uninterrupted line of the specified length
            lines.append((start_x, start_y, start_x + length, start_y))
    return lines
