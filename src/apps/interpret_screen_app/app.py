import asyncio
from queue import Empty

import PIL
from PIL import ImageTk, Image
import tkinter
import traceback

from common import ROOM_HEIGHT_IN_TILES, ROOM_WIDTH_IN_TILES, TILE_SIZE
from apps.util import tile_to_text, ScrollableFrame, QUEUE_POLL_INTERVAL

# The DROD room size is 836x704, use half that for canvas to preserve aspect ratio
_CANVAS_WIDTH = 418
_CANVAS_HEIGHT = 352
_LARGE_CANVAS_WIDTH = 836
_LARGE_CANVAS_HEIGHT = 704


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
    backend
        The backend that contains the play interface.
    """

    def __init__(self, root, event_loop, backend):
        super().__init__(root)
        self._main_window = root
        self._main_window.after(QUEUE_POLL_INTERVAL, self._check_queue)
        self._event_loop = event_loop
        self._backend = backend
        self._selected_view_step = tkinter.StringVar(self)
        self._enlarged_view = False
        self._debug_images = None
        self._radio_buttons = []
        self._room = None

        # Create widgets
        self._canvas = tkinter.Canvas(
            self, width=_CANVAS_WIDTH, height=_CANVAS_HEIGHT, bg="white"
        )
        self._canvas.bind("<Button-1>", self._clicked_canvas)
        self._canvas.pack(side=tkinter.LEFT)
        self._control_panel = tkinter.Frame(self)
        self._control_panel.pack(side=tkinter.RIGHT)
        self._tile_content = tkinter.Label(self._control_panel, text="")
        self._tile_content.pack(side=tkinter.TOP)
        self._room_text = tkinter.Label(self._control_panel, text="")
        self._room_text.pack(side=tkinter.TOP)
        self._get_view_buttons = tkinter.Frame(self._control_panel)
        self._get_view_buttons.pack(side=tkinter.TOP)
        self._get_view_button = tkinter.Button(
            self._get_view_buttons, text="Get view", command=self._get_view
        )
        self._get_view_button.pack(side=tkinter.LEFT)
        self._move_then_get_view_button = tkinter.Button(
            self._get_view_buttons,
            text="Move E, get view",
            command=self._move_then_get_view,
        )
        self._move_then_get_view_button.pack(side=tkinter.LEFT)
        self._toggle_view_size_button = tkinter.Button(
            self._control_panel, text="Enlarge view", command=self._toggle_view_size
        )
        self._toggle_view_size_button.pack(side=tkinter.TOP)
        self._debug_step_frame = ScrollableFrame(self._control_panel)
        self._debug_step_frame.pack(side=tkinter.TOP)

        self._set_debug_steps()

    def _check_queue(self):
        """Check the queue for updates."""
        try:
            data = self._backend.get_queue().get(block=False)
            self.set_data(*data)
        except Empty:
            pass
        self._main_window.after(QUEUE_POLL_INTERVAL, self._check_queue)

    def set_data(self, debug_images, room, room_text):
        """Set the data to show in the app.

        Parameters
        ----------
        debug_images
            A list of (name, image) pairs.
        room
            The room interpreted from the screenshot.
        room_text
            The text that popped up when entering the room.
        """
        self._debug_images = debug_images
        self._room = room
        self._room_text.config(text=f"Room text: {room_text.value}")
        self._set_debug_steps()
        self._draw_view()

    def _set_debug_steps(self):
        debug_steps = (
            [name for name, image in self._debug_images]
            if self._debug_images is not None
            else ["Screenshot"]
        )
        if self._selected_view_step.get() not in debug_steps:
            self._selected_view_step.set("Screenshot")

        for radio_button in self._radio_buttons:
            radio_button.pack_forget()
        self._radio_buttons = [
            tkinter.Radiobutton(
                self._debug_step_frame.scrollable_frame,
                text=step,
                value=step,
                variable=self._selected_view_step,
                command=self._draw_view,
            )
            for step in debug_steps
        ]
        for radio_button in self._radio_buttons:
            radio_button.pack(side=tkinter.TOP)

    def _draw_view(self):
        if self._debug_images is not None:
            step = self._selected_view_step.get()
            image = next(image for name, image in self._debug_images if name == step)
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

    def _get_view(self):
        self._run_coroutine(self._backend.get_view())

    def _move_then_get_view(self):
        self._run_coroutine(self._backend.move_then_get_view())

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
        step = self._selected_view_step.get()
        image = next(image for name, image in self._debug_images if name == step)
        if image.shape == (
            ROOM_HEIGHT_IN_TILES * TILE_SIZE,
            ROOM_WIDTH_IN_TILES * TILE_SIZE,
            3,
        ):
            tile = self._room.get_tile((x, y))
            self._tile_content.config(text=tile_to_text(tile))
        elif step == "Extract minimap":
            color = next(
                image for name, image in self._debug_images if name == "Extract minimap"
            )[y, x, :]
            self._tile_content.config(text=str(color))
