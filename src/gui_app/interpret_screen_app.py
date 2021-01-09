import asyncio

import PIL
from PIL import ImageTk, Image
import tkinter
import traceback

from common import (
    ImageProcessingStep,
    TILE_SIZE,
)
from .util import tile_to_text, annotate_room_image_with_tile_contents

# The DROD room size is 836x704, use half that for canvas to preserve aspect ratio
CANVAS_WIDTH = 418
CANVAS_HEIGHT = 352
LARGE_CANVAS_WIDTH = 836
LARGE_CANVAS_HEIGHT = 704


class InterpretScreenApp(tkinter.Frame):
    """This app is used to debug the interpretation of the screenshots.

    It takes screenshots and shows them at specified steps in the image
    processing process.

    Parameters
    ----------
    root
        The parent of the tkinter Frame.
    event_loop
        The asyncio event loop for the backend thread.
    interface
        The play interface, used to get and process screenshots.
    """

    def __init__(self, root, event_loop, interface):
        super().__init__(root)
        self._event_loop = event_loop
        self._interface = interface
        self._selected_view_step = tkinter.StringVar(self)
        self._selected_view_step.set(list(ImageProcessingStep)[-1].value)
        self._enlarged_view = False
        self._raw_view_image = None
        self._room = None

        # Create widgets
        self._canvas = tkinter.Canvas(
            self, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg="white"
        )
        self._canvas.bind("<Button-1>", self._clicked_canvas)
        self._canvas.pack(side=tkinter.LEFT)
        self._control_panel = tkinter.Frame(self)
        self._control_panel.pack(side=tkinter.RIGHT)
        self._toggle_view_size_button = tkinter.Button(
            self._control_panel, text="Enlarge view", command=self._toggle_view_size
        )
        self._toggle_view_size_button.pack(side=tkinter.BOTTOM)
        self._get_view = tkinter.Button(
            self._control_panel, text="Get view", command=self._show_view
        )
        self._get_view.pack(side=tkinter.BOTTOM)
        self._view_step_dropdown = tkinter.OptionMenu(
            self._control_panel,
            self._selected_view_step,
            *[s.value for s in ImageProcessingStep]
        )
        self._view_step_dropdown.pack(side=tkinter.BOTTOM)
        self._tile_content = tkinter.Label(self._control_panel, text="")
        self._tile_content.pack(side=tkinter.BOTTOM)

    def set_data(self, image, room=None):
        """Set the data to show in the app.

        Parameters
        ----------
        image
            The image to show.
        room
            If given, annotate the tiles in the image with their contents,
            as they appear in this room.
        """
        self._raw_view_image = image
        self._room = room
        self._draw_view()

    def _draw_view(self):
        if self._raw_view_image is not None:
            if self._room is not None:
                # Let's assume the image is of the room here. If that is not the case,
                # the below function will produce weird results.
                image = annotate_room_image_with_tile_contents(
                    self._raw_view_image, self._room
                )
            else:
                image = self._raw_view_image
            pil_image = PIL.Image.fromarray(image)
            resized_image = pil_image.resize(
                (int(self._canvas["width"]), int(self._canvas["height"])), Image.NEAREST
            )
            # Assign to self._view to prevent from being garbage collected
            self._view = ImageTk.PhotoImage(image=resized_image)
            self._canvas.create_image(0, 0, image=self._view, anchor=tkinter.NW)

    def _run_coroutine(self, coroutine):
        async def wrapped_coroutine():
            try:
                await coroutine
            except Exception:
                traceback.print_exc()

        asyncio.run_coroutine_threadsafe(wrapped_coroutine(), self._event_loop)

    def _show_view(self):
        step_value = self._selected_view_step.get()
        step = next(e for e in ImageProcessingStep if e.value == step_value)
        self._run_coroutine(self._interface.show_view_step(step))

    def _toggle_view_size(self):
        if self._enlarged_view:
            self._enlarged_view = False
            self._canvas.configure(height=CANVAS_HEIGHT, width=CANVAS_WIDTH)
            self._toggle_view_size_button.configure(text="Enlarge view")
            self._draw_view()
        else:
            self._enlarged_view = True
            self._canvas.configure(height=LARGE_CANVAS_HEIGHT, width=LARGE_CANVAS_WIDTH)
            self._toggle_view_size_button.configure(text="Ensmall view")
            self._draw_view()

    def _clicked_canvas(self, event):
        if self._enlarged_view:
            x = event.x // TILE_SIZE
            y = event.y // TILE_SIZE
        else:
            x = event.x // (TILE_SIZE // 2)
            y = event.y // (TILE_SIZE // 2)
        if self._room is not None:
            tile = self._room.get_tile((x, y))
            self._tile_content.config(text=tile_to_text(tile))
        elif self._raw_view_image.shape == (32, 38, 3):
            # This is probably the minimap, so showing the color is nice
            color = self._raw_view_image[y, x, :]
            self._tile_content.config(text=str(color))
