import padKontrol as pk
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

from .baseState import State
import time
from .drumpattern import Drumpattern
import threading
from decorators import *
import midi_ports as mp


class ReDrumState(State, threading.Thread):
    state_name = "rEd"

    def __init__(self):
        super(ReDrumState, self).__init__()
        threading.Thread.__init__(self)
        self.hotkeys = set()
        self.channel = 1
        # self.bpm = max(20, min(bpm, 400))
        self.bpm = 120
        self.interval = 15.0 / self.bpm
        self.pattern = Drumpattern()
        self.done = False
        self.daemon = True  # Allow main to exit even if still running.
        self.paused = True  # Start out paused.
        self.state = threading.Condition()
        self.callcount = 0
        self.started = time.time()

    def load_state(self):
        mp.light_blink(pk.BUTTON_VELOCITY)
        if not self.is_alive():
            self.start()
            self.pattern.initialize()
        self.pattern.load_current_instrument()

    def handle_button(self, sysEx):
        if sysEx.control == pk.BUTTON_VELOCITY:
            self.handle_pause(sysEx)
        elif sysEx.control == pk.BUTTON_REL_VAL:
            self.reset(sysEx)
        elif sysEx.control == pk.BUTTON_HOLD:
            self.pattern.next_instrument(sysEx)
        elif sysEx.control == pk.BUTTON_ROLL:
            self.pattern.prev_instrument(sysEx)

    def handle_pad(self, sysEx):
        self.pattern.handle_step(sysEx)

    def handle_rotary(self, sysEx):
        if sysEx.data == 1:
            self.bpm += 1
        else:
            self.bpm -= 1
        self.interval = 15.0 / self.bpm
        mp.led(self.bpm)

    @action_on_press(False)
    def handle_pause(self, sysEx):
        print(sysEx)
        if self.paused:
            self.resume_seq(sysEx)
        else:
            self._pause_seq(sysEx)

    @press_light
    def resume_seq(self, sysEx):
        # mp.light_off(self.pattern.step)
        with self.state:
            self.paused = False
            self.started = time.time()

            self.callcount = 0
            self.state.notify()  # Unblock self if waiting.

    @blink_light
    def _pause_seq(self, sysEx):
        self._pause()

    def _pause(self):
        with self.state:
            print("paused")
            self.paused = True  # Block self.

    @press_light
    @action_on_press(False)
    def reset(self, sysEx):
        if self.paused:
            self.pattern.reset()

    def main_loop(self):
        self.worker()
        self.callcount += 1

        # Compensate for drift:
        sleep_duration = (self.callcount) * self.interval - time.time() + self.started

        if sleep_duration > 0:
            time.sleep(sleep_duration)

    def run(self):
        mp.send_midi(
            dict(
                type="control_change",
                channel=self.channel,
                control=ALL_SOUND_OFF,
                value=0,
            )
        )

        # give MIDI instrument some time to activate drumkit
        time.sleep(0.3)

        while not self.done:
            with self.state:
                if self.paused:
                    mp.send_midi(
                        dict(
                            type="control_change",
                            channel=self.channel,
                            control=ALL_SOUND_OFF,
                            value=0,
                        )
                    )
                    self.state.wait()  # Block execution until notified.
            # Do stuff.
            self.main_loop()

        mp.send_midi(
            dict(
                type="control_change",
                channel=self.channel,
                control=ALL_SOUND_OFF,
                value=0,
            )
        )

    def worker(self):
        """Variable time worker function.
        i.e., output notes, emtpy queues, etc.
        """

        self.pattern.playstep(self.bpm, self.channel)
