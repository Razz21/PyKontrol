from States.baseState import StateBase
import padKontrol as pk
import time


from rtmidi.midiconstants import (
    ALL_SOUND_OFF,
    BANK_SELECT_LSB,
    BANK_SELECT_MSB,
    CHANNEL_VOLUME,
    CONTROL_CHANGE,
    NOTE_ON,
    NOTE_OFF,
    PROGRAM_CHANGE,
)


class FreeState(StateBase):
    _name = "st1"
    ordered = [
        12,
        13,
        14,
        15,
        8,
        9,
        10,
        11,
        4,
        5,
        6,
        7,
        0,
        1,
        2,
        3,
    ]  # pad order left-right / down-up

    def __init__(self,):
        super().__init__()
        self.hotkeys = set()
        self.channel = 1
        self._transpose = 12

    @property
    def transpose(self):
        return self._transpose

    @transpose.setter
    def transpose(self, val):
        self._transpose = max(min(28, val), 0)

    def handle_pad(self, sysEx):
        self.pad_on(sysEx)

    def handle_button(self, sysEx):
        if sysEx.control == pk.BUTTON_HOLD:
            self.handle_transpose(sysEx, 1)
        if sysEx.control == pk.BUTTON_ROLL:
            self.handle_transpose(sysEx, 0)
        if sysEx.control == pk.BUTTON_FLAM:
            self.handle_transpose(sysEx)

    def handle_rotary(self, sysEx):
        pass

    def handle_knob(self, sysEx):
        pass

    def handle_xy_pad(self, sysEx):
        pass

    @StateBase.press_light
    def pad_on(self, sysEx):
        pad = self.ordered[sysEx.control]
        self.send_midi(
            dict(
                type=sysEx.state,
                channel=self.channel,
                note=pad + 4 * self.transpose,
                velocity=sysEx.data,
            )
        )

    def play_note(self, control):
        pad = self.ordered[control]
        self.send_midi(
            dict(
                type=pk.NOTE_ON,
                channel=self.channel,
                note=pad + 4 * self.transpose,
                velocity=0,
            )
        )
        self.light_on(control)

    def handle_transpose(self, sysEx, mode=2):
        if sysEx.state == pk.NOTE_ON:
            if mode == 0:
                self.transpose -= 1
            elif mode == 1:
                self.transpose += 1
            else:
                self.transpose = 12
            self.light_on(sysEx.control)
            self.led(self.translate_to_led(self.transpose))
        else:
            self.light_off(sysEx.control)
            self.led(self.name)

    def _start(self):
        print("started", self._name)
