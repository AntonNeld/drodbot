import asyncio
import tkinter
import traceback

from common import Strategy


class PlayingApp(tkinter.Frame):
    """This app is used to make DRODbot actually play DROD.

    Parameters
    ----------
    root
        The parent of the tkinter Frame.
    event_loop
        The asyncio event loop for the backend thread.
    backend
        The backend containing the DRODbot.
    """

    def __init__(self, root, event_loop, backend):
        super().__init__(root)
        self._event_loop = event_loop
        self._backend = backend
        self._data = None
        self._selected_strategy = tkinter.StringVar(self)
        self._selected_strategy.set(list(Strategy)[0].value)

        # Create widgets
        self._control_panel = tkinter.Frame(self)
        self._control_panel.pack(side=tkinter.RIGHT)
        self._run_controls = tkinter.Frame(self._control_panel)
        self._run_controls.pack(side=tkinter.TOP)
        self._strategy_dropdown = tkinter.OptionMenu(
            self._run_controls, self._selected_strategy, *[s.value for s in Strategy]
        )
        self._strategy_dropdown.pack(side=tkinter.LEFT)
        self._go = tkinter.Button(
            self._run_controls, text="Go", command=self._run_strategy
        )
        self._go.pack(side=tkinter.RIGHT)
        self._save_state_button = tkinter.Button(
            self._control_panel, text="Save state", command=self._save_state
        )
        self._save_state_button.pack(side=tkinter.TOP)

    def set_data(self, data):
        """Set the DRODbot state to show in the app.

        Parameters
        ----------
        data
            The DRODbot state.
        """
        self._data = data

    def _run_coroutine(self, coroutine):
        async def wrapped_coroutine():
            try:
                await coroutine
            except Exception:
                traceback.print_exc()

        asyncio.run_coroutine_threadsafe(wrapped_coroutine(), self._event_loop)

    def _run_strategy(self):
        strategy_value = self._selected_strategy.get()
        strategy = next(e for e in Strategy if e.value == strategy_value)
        self._run_coroutine(self._backend.run_strategy(strategy))

    def _save_state(self):
        self._run_coroutine(self._backend.save_state())
