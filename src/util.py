import numpy


def find_color(image, color):
    """Find all pixels with a specific color.

    Parameters
    ----------
    image
        The image to find the color in.
    color
        The color to find.

    Returns
    -------
    A boolean 2D numpy array, which is True where the image
    has the color and False elsewhere.
    """
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
