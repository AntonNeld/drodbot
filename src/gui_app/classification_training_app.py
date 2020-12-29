import asyncio
import tkinter
import traceback


class ClassificationTrainingApp(tkinter.Frame):
    def __init__(self, root, event_loop, trainer):
        super().__init__(root)
        self.root = root
        self.event_loop = event_loop
        self.trainer = trainer
        self.create_widgets()

    def create_widgets(self):
        self.procure_training_data_button = tkinter.Button(
            self,
            text="Procure training data",
            command=self.procure_training_data,
        )
        self.procure_training_data_button.pack()

    def run_coroutine(self, coroutine):
        async def wrapped_coroutine():
            try:
                await coroutine
            except Exception:
                traceback.print_exc()

        asyncio.run_coroutine_threadsafe(wrapped_coroutine(), self.event_loop)

    def procure_training_data(self):
        self.run_coroutine(self.trainer.procure_training_data())
