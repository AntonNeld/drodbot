import asyncio
import tkinter
import traceback


class ClassificationTrainingApp(tkinter.Frame):
    def __init__(self, root, event_loop, trainer):
        super().__init__(root)
        self.root = root
        self.event_loop = event_loop
        self.trainer = trainer
        self.data = None
        self.create_widgets()

    def create_widgets(self):
        self.procure_training_data_button = tkinter.Button(
            self,
            text="Procure training data",
            command=self.procure_training_data,
        )
        self.procure_training_data_button.pack(side=tkinter.TOP)
        self.load_training_data_button = tkinter.Button(
            self,
            text="Load training data",
            command=self.load_training_data,
        )
        self.load_training_data_button.pack(side=tkinter.TOP)

    def set_data(self, data):
        self.data = data

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
