import asyncio
import queue
import threading
import tkinter

from classification_trainer import ClassificationTrainer
from drod_bot import DrodBot
from drod_interface import DrodInterface
from gui_app import GuiApp


if __name__ == "__main__":
    window_queue = queue.Queue()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    asyncio_thread = threading.Thread(target=loop.run_forever)
    asyncio_thread.start()

    interface = DrodInterface()
    trainer = ClassificationTrainer("training_data", interface)
    bot = DrodBot(interface, window_queue)

    window = tkinter.Tk()
    app = GuiApp(
        root=window, event_loop=loop, queue=window_queue, bot=bot, trainer=trainer
    )
    app.pack()
    try:
        app.mainloop()
    finally:
        loop.call_soon_threadsafe(loop.stop)
        asyncio_thread.join()
