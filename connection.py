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

log = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s,%(msecs)d %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)

# should be named 'padKONTROL 1 CTRL' or similar.
OUTPUT_MIDI_PORT = 2
# should be named 'padKONTROL 1 PORT A' or similar
INPUT_MIDI_PORT = 1


class PadKontrolHandler:
    def __init__(self, midi_in, midi_out, pk_print):
        self.midi_in = midi_in
        self.midi_out = midi_out
        self.pk_print = pk_print

    # def send_sysex(self, sysex):
    #     self.midi_out.send_message(sysex)
    #     logging.info(sysex)
        
        # def _midi_in_callback(self, message, data):
        #     sysex_buffer = []
        #     for byte in message[0]:
        #         sysex_buffer.append(byte)
        #         if byte == 0xF7:
        #             self.pk_print.process_sysex(sysex_buffer)
        #             del sysex_buffer[:]

    def send_sysex(self, sysex):
        logging.info(sysex)
        sysex = mido.parse_string(sysex)
        self.midi_out.send(sysex)

    def _midi_in_callback(self, message):
        sysex_buffer = []
        for byte in message.bytes():
            sysex_buffer.append(byte)
            if byte == 0xF7:
                self.pk_print.process_sysex(sysex_buffer)
                del sysex_buffer[:]

    def _initialize_connection(self):
        # todo initialization logs
        self.send_sysex(pk.SYSEX_NATIVE_MODE_OFF)
        self.send_sysex(pk.SYSEX_NATIVE_MODE_ON)
        self.send_sysex(pk.SYSEX_NATIVE_MODE_ENABLE_OUTPUT)
        self.send_sysex(pk.SYSEX_NATIVE_MODE_INIT)
        self.send_sysex(pk.SYSEX_NATIVE_MODE_TEST)
        # these sysex messages are device specyfic and input port must ignore them
        # wait some time to avoid conflicts  between I/O ports
        time.sleep(0.5)
        # self.midi_in.ignore_types(False, False, False)  # enable sysex messages listener
        self.midi_in._rt.ignore_types(False, False, False)
        self.midi_in.callback = self._midi_in_callback

    def _close_connection(self):
        self.send_sysex(pk.SYSEX_NATIVE_MODE_OFF)


class HostKontrolHandler:
    def __init__(self, midi_out, midi_in=None):
        self.midi_in = midi_in
        self.midi_out = midi_out

    def send_midi(self, data):
        self.midi_out.send(data)


class Context:
    _state = None

    _states = deque()

    def __init__(self, pk_handler, host_handler):
        self._pk_handler = pk_handler
        self._host_handler = host_handler

    def load_state(self):
        self._state = self._states[0]
        self._state.context = self
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

    def send_sysex(self, sysex):
        self._pk_handler.send_sysex(sysex)

    def send_midi(self, data):
        self._host_handler.send_midi(data)

    def _initialize_connection(self):
        self._pk_handler._initialize_connection()
        self.load_state()

    def _close_connection(self):
        self._pk_handler._close_connection()


# ------------------------------------------

# midi_out, _ = open_midioutput(
#     OUTPUT_MIDI_PORT,
#     api=rtmidi.API_WINDOWS_MM,
#     client_name="padkontrol",
#     port_name="MIDI Out",
# )


# midi_in, _ = open_midiinput(
#     INPUT_MIDI_PORT,
#     api=rtmidi.API_WINDOWS_MM,
#     client_name="padkontrol",
#     port_name="MIDI In",
# )

# host_midiout = rtmidi.MidiOut()  # send midi to host
# available_ports = host_midiout.get_ports()

# try:
#     host_midiout.open_port(5)
# except:
#     pass

midi_out = mp.get_padkontrol_output()
midi_in = mp.get_padkontrol_input()
host_midiout = mp._get_midi_out_data()

# initialize I/O handler objects
pk_print = PadKontrolPrint()
pk_handler = PadKontrolHandler(midi_in=midi_in, midi_out=midi_out, pk_print=pk_print)
host_handler = HostKontrolHandler(host_midiout)

# crete states
state1 = FreeState()
# state2 = ReDrumState()

# initialize Context object and add states objects
c = Context(pk_handler, host_handler)
c.add_state(state1)

# register Context as main listener
pk_print.register(c)

input("Press enter to initialize connection")
# create connection with device
c._initialize_connection()

# ready to fun
input("Press enter to exit")

# c.close_connection()
c._close_connection()
midi_in.close()
midi_out.close()
host_midiout.close()
