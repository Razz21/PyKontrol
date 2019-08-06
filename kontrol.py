#!/usr/bin/env python

import padKontrol as pk
import rtmidi
from rtmidi.midiutil import open_midioutput, open_midiinput
import pkconstants as const
import time

import string
from collections import deque

from kontrol_modes import Mode1, Mode2, Mode3

# should be named 'padKONTROL 1 CTRL' or similar.
OUTPUT_MIDI_PORT = 2
# should be named 'padKONTROL 1 PORT A' or similar
INPUT_MIDI_PORT = 1

midi_out, _ = open_midioutput(
    OUTPUT_MIDI_PORT,
    api=rtmidi.API_UNIX_JACK,
    client_name="padkontrol",
    port_name="MIDI Out",
)


def send_sysex(sysex):
    midi_out.send_message(sysex)

class PadKontrolPrint(pk.PadKontrolInput):
    def __init__(self,):
        super().__init__()
        self._listener = None

    def on_pad_down(self, pad, velocity):
        print("pad #%d down, velocity %d/127" % (pad, velocity))
        self.send_msg(("pad", pad, 1, velocity))

    def on_pad_up(self, pad):
        print("pad #%d up" % pad)
        self.send_msg(("pad", pad, 0))

    def on_button_down(self, button):
        if button == const.BUTTON_FLAM:
            print("flam button down")
        else:
            print("button #%d down" % button)
        self.send_msg(("button", button, 1))

    def on_button_up(self, button):
        if button == const.BUTTON_MESSAGE:
            print("message button up")
        else:
            print("button #%d up" % button)

        self.send_msg(("button", button, 0))

    def on_knob(self, knob, value):
        print("knob #%d value = %d" % (knob, value))
        self.send_msg(("knob", knob, value))

    # def on_rotary_left(self):
    #     print("rotary turned left")
    #     self.send_msg(("rotary", const.ROTARY_KNOB, 0))

    # def on_rotary_right(self):
    #     print("rotary turned right")
    #     self.send_msg(("rotary", const.ROTARY_KNOB, 1))

    def on_rotary(self, val):
        print("ON ROTARY", val)
        # val: left = 127, right = 1
        self.send_msg(("rotary", const.ROTARY_KNOB, 1, val))

    def on_x_y(self, x, y):
        print("x/y pad (x = %d, y = %d)" % (x, y))
        self.send_msg(("x/y", const.BUTTON_PAD, x, y))

    def register(self, listener):
        self._listener = listener

    def send_msg(self, msg):
        self._listener.notify(msg)


send_sysex(const.SYSEX_NATIVE_MODE_OFF)

input("Press enter to enable native mode.")

send_sysex(const.SYSEX_NATIVE_MODE_ON)  # must be sent first
send_sysex(const.SYSEX_NATIVE_MODE_ENABLE_OUTPUT)
send_sysex(const.SYSEX_NATIVE_MODE_INIT)  # must be sent after SYSEX_NATIVE_MODE_ON
send_sysex(const.SYSEX_NATIVE_MODE_TEST)  # displays 'YES' on the LED

input(
    "Press enter to demonstrate input handling (then enter again to exit this example)."
)


class Handler:
    KNOBS = [const.ROTARY_KNOB, const.KNOB_1, const.KNOB_2]
    RESERVED_CONTROLLERS = [const.BUTTON_KNOB_1_ASSIGN, const.BUTTON_KNOB_2_ASSIGN]

    def __init__(self, *args, **kwargs):
        self.publisher = None
        self.midiout = kwargs.get("midiout", None)
        self.current_mode = None  # set default
        self.hotkeys = set()
        # deque allows to iterate in infite loop through list in any way
        self.__modes = deque()
        self.__COMBINATIONS = {
            frozenset([const.BUTTON_SETTING, const.ROTARY_KNOB]): self.hotkey_found
        }

    def load_mode(self):
        self.current_mode = self.__modes[0]
        send_sysex(pk.led(self.current_mode.name))
        # TODO reset previous mode state/ lights/ messages etc...

    def change_mode(self, state):
        """
        replace current mode
        state: receive knob rotation value
        1 - turning right / 127 - turning left
        """
        position = -1
        if state == const.ROTARY_KNOB_LEFT:
            position = 1
        self.__modes.rotate(position)
        self.load_mode()

    def hotkey_found(self):
        print("found hotkey!!")

    def add_modes(self, *args):
        self.__modes.extend(args)
        self.load_mode()

    def handle_default_action(self, msg):
        """
        global default actions here
        """
        group, symbol, state, *data = msg
        if symbol == const.ROTARY_KNOB:
            self.change_mode(*data)

    def catch_global_action(self, msg):
        """
        Catch combo or fire default global action for reserved knobs/buttons.
        Check action flow:
        global combination -> default global action -> modes actions
        Return:
            True, global event is firing and blocks modes actions,
            False, global action not used, pass message to active mode
        """

        group, symbol, state, *data = msg
        catched = False

        if state:
            # catch combination if button pressed or knob turned
            self.hotkeys.add(symbol)
            if frozenset(self.hotkeys) in self.__COMBINATIONS:
                self.__COMBINATIONS[frozenset(self.hotkeys)]()
                catched = True
            else:
                self.handle_default_action(msg)
        else:
            # remove from hotkeys queue on release
            self.hotkeys.discard(symbol)

        # knobs do not send on/off state,
        # must be removed from hotkey queue every turn
        if symbol in self.KNOBS:
            self.hotkeys.discard(symbol)

        return catched

    def notify(self, msg):
        """
        handle global events and button combinations:
        - change mode
        or dispatch message to active mode`s message handler
        """
        if msg[1] in self.RESERVED_CONTROLLERS:  # check byte
            self.handle_default_action(msg)
        else:
            catched = self.catch_global_action(msg)
            if not catched:
                # pass signal to active mode handler
                self.current_mode.handle_event(msg)

        # if type == "button":
        #     button, = data
        #     if state:
        #         if button == const.BUTTON_HOLD:
        #             send_sysex(pk.light(button, const.LIGHT_STATE_ON))
        #             text = "longer message"
        #             for i in range(len(text) - 2):
        #                 x = text[i : i + 3]
        #                 time.sleep(0.3)
        #                 send_sysex(pk.led(x))
        #         else:
        #             send_sysex(pk.light_flash(button, 1.0))
        #     else:
        #         send_sysex(pk.light(button, const.LIGHT_STATE_OFF))
        #         send_sysex(pk.led("off"))
        # if type == "pad":
        #     ordered = [
        #         12,
        #         13,
        #         14,
        #         15,
        #         8,
        #         9,
        #         10,
        #         11,
        #         4,
        #         5,
        #         6,
        #         7,
        #         0,
        #         1,
        #         2,
        #         3,
        #     ]  # pad order left-right / down-up
        #     if state:
        #         pad, velocity = data
        #         send_sysex(pk.light_flash(pad, 0.5))
        #         if self.midiout:
        #             midiout.send_message(
        #                 [144, 48 + ordered[pad], velocity]
        #             )  # channel 1, middle C, velocity
        #     else:
        #         pad, = data
        #         if self.midiout:
        #             midiout.send_message([128, 48 + ordered[pad], 0])
        #     print(pad)


midi_in, _ = open_midiinput(
    INPUT_MIDI_PORT,
    api=rtmidi.API_UNIX_JACK,
    client_name="padkontrol",
    port_name="MIDI In",
)

midiout = rtmidi.MidiOut()
available_ports = midiout.get_ports()
print(available_ports)

midiout.open_port(5)


pk_print = PadKontrolPrint()

m1 = Mode1()
m2 = Mode2()
m3 = Mode3()
handler = Handler(midiout=midiout)
handler.add_modes(m1, m2, m3)
pk_print.register(handler)


def midi_in_callback(message, data):

    sysex_buffer = []
    for byte in message[0]:
        sysex_buffer.append(byte)

        if byte == 0xF7:
            pk_print.process_sysex(sysex_buffer)
            del sysex_buffer[:]  # empty list


midi_in.ignore_types(False, False, False)
midi_in.set_callback(midi_in_callback)

input("Press enter to exit")

send_sysex(const.SYSEX_NATIVE_MODE_OFF)

midi_in.close_port()
midi_out.close_port()
midiout.close_port()

# input("Press enter to display blinking numbers.")

# send_sysex(pk.led("123", const.LED_STATE_BLINK))

# input("Press enter to display a greeting.")

# welcome_message = pk.string_to_sysex("Hi ")

# send_sysex(pk.led(welcome_message))

# input("Press enter to see the PROG CHANGE button flash once.")

# send_sysex(pk.light_flash(const.BUTTON_PROG_CHANGE, 0.5))

# input("Press enter to see pad #4 blink.")

# send_sysex(pk.light(4, const.LIGHT_STATE_BLINK))

# input("Press enter to light up the KNOB 1 ASSIGN button.")

# send_sysex(pk.light(const.BUTTON_KNOB_1_ASSIGN, True))

# input("Press enter to turn off pad #4 and the KNOB 1 ASSIGN lights.")

# send_sysex(pk.light(4, False))
# send_sysex(pk.light(const.BUTTON_KNOB_1_ASSIGN, const.LIGHT_STATE_OFF))

# input("Press enter to turn on multiple lights with one message.")

# send_sysex(pk.light_group("PAD", dict.fromkeys(const.ALL_PADS, True)))

# input("press to light only buttons")
# send_sysex(pk.light_group("Off", dict.fromkeys(const.ALL_BUTTONS_AND_PADS, False)))
# send_sysex(pk.light_group("On ", dict.fromkeys(const.ALL_BUTTONS, True)))


# input("press to turn lights off")
# send_sysex(pk.light_group("Off", dict.fromkeys(const.ALL_BUTTONS_AND_PADS, False)))

