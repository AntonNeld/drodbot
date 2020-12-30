import asyncio
import queue
import threading
import tkinter

from tile_classifier import TileClassifier
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
    classifier = TileClassifier(
        "training_data", "model_weights", interface, window_queue
    )
    bot = DrodBot(interface, window_queue)

    window = tkinter.Tk()
    app = GuiApp(
        root=window, event_loop=loop, queue=window_queue, bot=bot, classifier=classifier
    )
    app.pack()
    try:
        app.mainloop()
    finally:
        loop.call_soon_threadsafe(loop.stop)
        asyncio_thread.join()
