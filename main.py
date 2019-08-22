#!/usr/bin/env python

import padKontrol as pk
import rtmidi
from rtmidi.midiutil import open_midioutput, open_midiinput
import time
import mido
import string
from collections import deque
import logging
from kontrol_listener import PadKontrolPrint
import midi_ports as mp
from States.free import FreeState
from States.redrum import ReDrumState

# log = logging.getLogger(__name__)
# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s,%(msecs)d %(levelname)s: %(message)s",
#     datefmt="%H:%M:%S",
# )


class Context:
    """Store reference to all and active state
    """

    _state = None
    _states = deque()

    def load_state(self):
        self._state = self._states[0]
        self._state._context = self
        self._state.load_state()

    def next_state(self):
        position = -1
        self._states.rotate(position)
        self.load_state()

    def previous_state(self):
        position = 1
        self._states.rotate(position)
        self.load_state()

    def add_state(self, *args):
        self._states.extend(args)

    def notify(self, msg):
        self._state.handle_event(msg)


# ------------------------------------------
def main():
    pk_print = PadKontrolPrint()

    # initialize Context object and add states objects
    c = Context()
    mp.connect()

    state1 = FreeState()
    state2 = ReDrumState()

    c.add_state(state1, state2)

    # register Context as main listener
    pk_print.register(c)

    input("Press enter to initialize connection")
    mp.start_native(pk_print.callback)
    c.load_state()
    input("Press enter to exit")

    mp.close_native()


main()
