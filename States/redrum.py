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

from .baseState import StateBase
import time
from .drumpattern import Drumpattern
import threading
from decorators import *
import midi_ports as mp


def next_time(t0, dt):
    while 1:
        t0 += dt
        yield t0


class ReDrumState(StateBase, threading.Thread):
    state_name = "rEd"
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

    def __init__(self):
        super(ReDrumState, self).__init__()
        threading.Thread.__init__(self)
        self.hotkeys = set()
        self.channel = 1
        # self.bpm = max(20, min(bpm, 400))
        self.bpm = 120
        self.interval = 15.0 / self.bpm
        self.pattern = Drumpattern()
        self.volume = 127
        self.done = False
        self.daemon = True  # Allow main to exit even if still running.
        self.paused = True  # Start out paused.
        self.state = threading.Condition()
        self.callcount = 0
        self.started = time.time()
        self.timer = next_time(time.time(), 0.5)

    def load_state(self):
        # mp.led(self.state_name)
        mp.light_blink(pk.BUTTON_VELOCITY)
        if not self.is_alive():
            self.start()
            self.pattern.initialize()
        self.pattern.load_current_instrument()

    def handle_button(self, sysEx):
        if sysEx.control == pk.BUTTON_VELOCITY:
            self.handle_pause(sysEx)
        if sysEx.control == pk.BUTTON_HOLD:
            self.pattern.next_instrument(sysEx)
        if sysEx.control == pk.BUTTON_ROLL:
            self.pattern.prev_instrument(sysEx)

    def handle_pad(self, sysEx):
        self.pattern.handle_step(sysEx)

    @press_light
    def resume_seq(self, sysEx):
        mp.light_off(self.pattern.step)
        with self.state:
            self.paused = False

            self.started = time.time()
            self.timer = next_time(time.time(), 0.125)

            self.callcount = 0
            self.state.notify()  # Unblock self if waiting.

    @action_on_press(False)
    def handle_pause(self, sysEx):
        print(sysEx)
        if self.paused:
            self.resume_seq(sysEx)
        else:
            self._pause_seq(sysEx)


    def handle_rotary(self, sysEx):
        if sysEx.data == 1:
            self.bpm += 1
        else:
            self.bpm -= 1
        self.interval = 15.0 / self.bpm
        mp.led(self.bpm)

    @blink_light
    def _pause_seq(self, sysEx):
        # mp.light_blink(self.pattern.step)
        self._pause()

    def _pause(self):
        with self.state:
            print("paused")
            self.paused = True  # Block self.

    def reset(self):
        # if self.paused:
        self.pattern.reset()

    def main_loop(self):
        self.worker()
        self.callcount += 1

        # Compensate for drift:
        sleep_duration = (self.callcount) * self.interval - time.time() + self.started
        
        if sleep_duration >0:
            time.sleep(sleep_duration)

    def run(self):
        # self.callcount = 0
        # self.activate_drumkit(self.pattern.kit)

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
            #     # Do stuff.

            self.main_loop()
            #

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

        self.pattern.playstep(self.channel)

    # def activate_drumkit(self, kit):

    #     if isinstance(kit, (list, tuple)):
    #         msb, lsb, pc = kit
    #     elif kit is not None:
    #         msb = lsb = None
    #         pc = kit

    # cc = CONTROL_CHANGE | self.channel
    # if msb is not None:
    #     mp.send_midi([cc, BANK_SELECT_MSB, msb & 0x7F])

    # if lsb is not None:
    #     mp.send_midi([cc, BANK_SELECT_LSB, lsb & 0x7F])

    # if kit is not None and pc is not None:
    #     mp.send_midi([PROGRAM_CHANGE | self.channel, pc & 0x7F])
