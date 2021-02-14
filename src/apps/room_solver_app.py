import asyncio

import PIL
from PIL import ImageTk, Image
import tkinter
import traceback

from common import TILE_SIZE
from .util import apparent_tile_to_text, annotate_room_image_with_tile_contents

# The DROD room size is 836x704, use half that for canvas to preserve aspect ratio
_CANVAS_WIDTH = 418
_CANVAS_HEIGHT = 352
_LARGE_CANVAS_WIDTH = 836
_LARGE_CANVAS_HEIGHT = 704


class RoomSolverApp(tkinter.Frame):
    """This app is used to debug the room solver.

    It takes a room and tries to solve it step by step.

    Parameters
    ----------
    root
        The parent of the tkinter Frame.
    event_loop
        The asyncio event loop for the backend thread.
    backend
        The backend that contains the play interface.
    """

    def __init__(self, root, event_loop, backend):
        super().__init__(root)
        self._event_loop = event_loop
        self._backend = backend
        self._enlarged_view = False
        self._room_image = None
        self._tile_contents = None

        # Create widgets
        self._canvas = tkinter.Canvas(
            self, width=_CANVAS_WIDTH, height=_CANVAS_HEIGHT, bg="white"
        )
        self._canvas.bind("<Button-1>", self._clicked_canvas)
        self._canvas.pack(side=tkinter.LEFT)
        self._control_panel = tkinter.Frame(self)
        self._control_panel.pack(side=tkinter.RIGHT)
        self._tile_content_text = tkinter.Label(self._control_panel, text="")
        self._tile_content_text.pack(side=tkinter.TOP)
        self._get_room_button = tkinter.Button(
            self._control_panel, text="Get room", command=self._get_room
        )
        self._get_room_button.pack(side=tkinter.TOP)
        self._toggle_view_size_button = tkinter.Button(
            self._control_panel, text="Enlarge view", command=self._toggle_view_size
        )
        self._toggle_view_size_button.pack(side=tkinter.TOP)
        self._simulate_move_east_button = tkinter.Button(
            self._control_panel,
            text="Simulate move east",
            command=self._simulate_move_east,
        )
        self._simulate_move_east_button.pack(side=tkinter.TOP)

    def set_data(self, room_image, tile_contents):
        """Set the data to show in the app.

        Parameters
        ----------
        room_image
            Real image of the current room.
        tile_contents
            The simulated contents of the tiles.
        """
        if room_image is not None:
            self._room_image = room_image
        if tile_contents is not None:
            self._tile_contents = tile_contents
        self._draw_view()

    def _draw_view(self):
        if self._room_image is not None:
            image = annotate_room_image_with_tile_contents(
                self._room_image, self._tile_contents
            )

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

    def _get_room(self):
        self._run_coroutine(self._backend.get_room())

    def _simulate_move_east(self):
        self._run_coroutine(self._backend.simulate_move_east())

    def _toggle_view_size(self):
        if self._enlarged_view:
            self._enlarged_view = False
            self._canvas.configure(height=_CANVAS_HEIGHT, width=_CANVAS_WIDTH)
            self._toggle_view_size_button.configure(text="Enlarge view")
            self._draw_view()
        else:
            self._enlarged_view = True
            self._canvas.configure(
                height=_LARGE_CANVAS_HEIGHT, width=_LARGE_CANVAS_WIDTH
            )
            self._toggle_view_size_button.configure(text="Ensmall view")
            self._draw_view()

    def _clicked_canvas(self, event):
        if self._enlarged_view:
            x = event.x // TILE_SIZE
            y = event.y // TILE_SIZE
        else:
            x = event.x // (TILE_SIZE // 2)
            y = event.y // (TILE_SIZE // 2)
        tile = self._tile_contents[(x, y)]
        self._tile_content_text.config(text=apparent_tile_to_text(tile))
