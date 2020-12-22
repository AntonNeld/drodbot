import asyncio
import threading
import tkinter

from drod_bot import DrodBot
from drod_interface import DrodInterface
from gui_app import GuiApp


if __name__ == "__main__":
    interface = DrodInterface()
    bot = DrodBot(interface)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    asyncio_thread = threading.Thread(
        target=loop.run_until_complete, args=(bot.move_randomly_forever(),)
    )
    window = tkinter.Tk()
    app = GuiApp(root=window)
    app.mainloop()
    asyncio_thread.start()
    try:
        asyncio_thread.join()
    except KeyboardInterrupt:
        # This will throw an ugly exception for now
        loop.call_soon_threadsafe(loop.stop)
        asyncio_thread.join()
