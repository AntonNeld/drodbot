import asyncio
import PIL
from PIL import ImageTk, Image
import tkinter
import traceback

from common import Direction

CANVAS_WIDTH = 88
CANVAS_HEIGHT = 88


class ClassificationTrainingApp(tkinter.Frame):
    def __init__(self, root, event_loop, trainer):
        super().__init__(root)
        self.root = root
        self.event_loop = event_loop
        self.trainer = trainer
        self.data = None
        self.create_widgets()

    def create_widgets(self):
        self.canvas = tkinter.Canvas(
            self, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg="white"
        )
        self.canvas.pack(side=tkinter.LEFT)

        self.details_area = tkinter.Frame(self)
        self.details_area.pack(side=tkinter.LEFT)
        self.tile_file_name = tkinter.Label(self.details_area, text="")
        self.tile_file_name.pack(side=tkinter.TOP)
        self.tile_content = tkinter.Label(self.details_area, text="")
        self.tile_content.pack(side=tkinter.TOP)

        self.control_panel = tkinter.Frame(self)
        self.control_panel.pack(side=tkinter.LEFT)
        self.procure_training_data_button = tkinter.Button(
            self.control_panel,
            text="Procure training data",
            command=self.procure_training_data,
        )
        self.procure_training_data_button.pack(side=tkinter.TOP)
        self.load_training_data_button = tkinter.Button(
            self.control_panel,
            text="Load training data",
            command=self.load_training_data,
        )
        self.load_training_data_button.pack(side=tkinter.TOP)

    def set_data(self, data):
        self.data = data
        self.show_tile(0)

    def show_tile(self, index):
        image = PIL.Image.fromarray(self.data[index]["image"])
        resized_image = image.resize(
            (int(self.canvas["width"]), int(self.canvas["height"])), Image.NEAREST
        )
        # Assign to self.tile_imagew to prevent from being garbage collected
        self.tile_image = ImageTk.PhotoImage(image=resized_image)
        self.canvas.create_image(0, 0, image=self.tile_image, anchor=tkinter.NW)

        self.tile_file_name.config(text=f"File: {self.data[index]['file_name']}")

        tile = self.data[index]["content"]
        lines = [
            f"Room piece: {format_element(tile.room_piece)}",
            f"Floor control: {format_element(tile.floor_control)}",
            f"Checkpoint: {format_element(tile.checkpoint)}",
            f"Item: {format_element(tile.item)}",
            f"Monster: {format_element(tile.monster)}",
            f"Swords: {','.join([format_element(sword) for sword in tile.swords])}",
        ]

        self.tile_content.config(text="\n".join(lines))

    def run_coroutine(self, coroutine):
        async def wrapped_coroutine():
            try:
                await coroutine
            except Exception:
                traceback.print_exc()

        asyncio.run_coroutine_threadsafe(wrapped_coroutine(), self.event_loop)

    def procure_training_data(self):
        self.run_coroutine(self.trainer.procure_training_data())

    def load_training_data(self):
        self.run_coroutine(self.trainer.load_training_data())


def format_element(pair):
    if pair is None:
        return ""
    element, direction = pair
    if direction == Direction.NONE:
        return element.value
    else:
        return f"{element.value} {direction.value}"
