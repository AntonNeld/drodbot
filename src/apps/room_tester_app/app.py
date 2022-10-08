from queue import Empty
from typing import List, Optional

import PIL
from PIL import ImageTk, Image
import tkinter
import numpy

from .backend import RoomTesterAppBackend, RoomTesterAppState
from common import TILE_SIZE
from apps.util import tile_to_text, ScrollableFrame, QUEUE_POLL_INTERVAL
from room_simulator import Room
from room_tester import Test

# The DROD room size is 836x704, use half that for canvas to preserve aspect ratio
_CANVAS_WIDTH = 418
_CANVAS_HEIGHT = 352
_LARGE_CANVAS_WIDTH = 836
_LARGE_CANVAS_HEIGHT = 704


class RoomTesterApp(tkinter.Frame):
    """This app is used to run regression tests.

    Parameters
    ----------
    root
        The parent of the tkinter Frame.
    backend
        The backend that contains the room tester.
    """

    def __init__(self, root: tkinter.Frame, backend: RoomTesterAppBackend):
        super().__init__(root)
        self._main_window = root
        self._main_window.after(QUEUE_POLL_INTERVAL, self._check_queue)
        self._backend = backend
        self._enlarged_view = False
        self._active_test_room: Optional[Room] = None
        self._active_test_room_image: Optional[numpy.ndarray] = None
        self._tests: List[Test] = []
        self._selected_active_test = tkinter.StringVar(self)

        self._radio_buttons: List[tkinter.Radiobutton] = []
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
        self._control_tests_frame = tkinter.Frame(self._control_panel)
        self._control_tests_frame.pack(side=tkinter.TOP)
        self._load_tests_button = tkinter.Button(
            self._control_tests_frame, text="Load tests", command=self._load_tests
        )
        self._load_tests_button.pack(side=tkinter.LEFT)
        self._toggle_view_size_button = tkinter.Button(
            self._control_panel, text="Enlarge view", command=self._toggle_view_size
        )
        self._toggle_view_size_button.pack(side=tkinter.TOP)
        self._tests_frame = ScrollableFrame(self._control_panel)
        self._tests_frame.pack(side=tkinter.TOP)

        self._set_tests()

    def _check_queue(self):
        """Check the queue for updates."""
        try:
            data = self._backend.get_queue().get(block=False)
            self.set_data(data)
        except Empty:
            pass
        self._main_window.after(QUEUE_POLL_INTERVAL, self._check_queue)

    def set_data(self, state: RoomTesterAppState):
        """Set the data to show in the app.

        Parameters
        ----------
        room
            The room interpreted from the screenshot.
        """
        self._active_test_room = state.active_test_room
        self._active_test_room_image = state.active_test_room_image
        self._tests = state.tests
        self._set_tests()
        self._draw_view()

    def _set_tests(self):
        if self._selected_active_test.get() not in [t.file_name for t in self._tests]:
            if len(self._tests) != 0:
                self._selected_active_test.set(self._tests[0].file_name)
                self._set_active_test()
            else:
                self._selected_active_test.set("notset")

        for radio_button in self._radio_buttons:
            radio_button.pack_forget()
        self._radio_buttons = [
            tkinter.Radiobutton(
                self._tests_frame.scrollable_frame,
                text=test.file_name,
                value=test.file_name,
                variable=self._selected_active_test,
                command=self._set_active_test,
            )
            for test in self._tests
        ]
        for radio_button in self._radio_buttons:
            radio_button.pack(side=tkinter.TOP)

    def _draw_view(self):
        if self._active_test_room_image is not None:
            pil_image = PIL.Image.fromarray(self._active_test_room_image)
            resized_image = pil_image.resize(
                (int(self._canvas["width"]), int(self._canvas["height"])), Image.NEAREST
            )
            # Assign to self._view to prevent from being garbage collected
            self._view = ImageTk.PhotoImage(image=resized_image)
            self._canvas.create_image(0, 0, image=self._view, anchor=tkinter.NW)

    def _load_tests(self):
        self._backend.load_tests()

    def _set_active_test(self):
        self._backend.set_active_test(self._selected_active_test.get())

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
        tile = self._active_test_room.get_tile((x, y))
        self._tile_content.config(text=tile_to_text(tile))
