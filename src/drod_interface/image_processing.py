import PIL
import numpy

# Also known as #203c4a
ROOM_UPPER_EDGE_COLOR = (32, 60, 74)


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


def pil_to_array(pil_image):
    return numpy.array(pil_image)


def array_to_pil(image):
    return PIL.Image.fromarray(image)
