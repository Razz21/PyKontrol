from States.baseState import State
import padKontrol as pk
import time
import utils
from collections import deque
from rtmidi.midiconstants import ALL_SOUND_OFF, ALL_NOTES_OFF
import midi_ports as mp
import decorators
from collections import deque
from math import isclose
from queue import Queue


class SetQueue(Queue):
    """Custom set type queue to remove duplicates
    """

    def _init(self, maxsize):
        self.queue = set()

    def _put(self, item):
        self.queue.add(item)

    def _get(self):
        return self.queue.pop()

    def __repr__(self):
        return f"{self.queue}"


class Strum:
    """Container for strum notes and velocities
    """

    def __init__(self, pitch, velocity):
        self.pitch = pitch
        self.velocity = velocity

    def __eq__(self, other):
        return self.pitch == other.pitch

    def __hash__(self):
        return hash(self.pitch)

    def __repr__(self):
        return f"({self.pitch}, {self.velocity})"


class Chords:
    """Container for strum chords
    """

    def __init__(self, pitch, notes=None):
        self.pitch = pitch
        self.notes = notes

    def add_note(self):
        pass

    def remove_note(self):
        pass

    def change_pitch(self):
        pass

    def get_notes(self):
        return self.notes[1]


class Strummer(State):
    state_name = "Str"
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
    strum_voicing = deque(
        [
            ("MAJOR", [0, 7, 12, 16, 19, 24]),
            ("MINOR", [0, 7, 12, 15, 19]),
            ("dIM", [0, 6, 9, 15]),
            ("Ad9", [0, 7, 12, 14, 19]),
            ("SU4", [0, 7, 12, 17, 19]),
            ("MA7", [0, 4, 10, 12, 16]),
            ("MI7", [0, 10, 15, 19]),
        ]
    )

    def __init__(self,):
        super().__init__()
        self.hotkeys = set()
        self._LOCAL_COMBINATIONS = {
            # frozenset([pk.BUTTON_PEDAL, pk.ROTARY_KNOB]): self.change_mode,
            # frozenset([pk.BUTTON_FLAM, pk.ROTARY_KNOB]): self.transpose_12,
            # frozenset([pk.BUTTON_PAD]): self.pitch_bend,
        }
        self.channel = 1
        self.led_text = None
        self.strum_queue = SetQueue()
        self.strum_chords = deque()
        self.strum = None
        self.chord = None
        self.strum_notes = None
        self.midiout = mp.get_midi_out_data()

    def load_state(self):
        # TODO scale pattern
        mp.led(self.state_name)
        major_scale = utils.pattern_to_scale([0, 2, 2, 1, 2, 2, 2, 1])
        for idx, n in enumerate(major_scale):
            if idx in [0, 3, 4, 7]:  # first, fourth and fifth
                notes = self.strum_voicing[0]
            elif idx == 6:  # leading note
                notes = self.strum_voicing[2]
            else:
                notes = self.strum_voicing[1]

            i = Chords(pitch=48 + n, notes=notes)
            self.strum_chords.append(i)
        self.load_strum(0)

    def load_strum(self, x):
        try:
            self.strum = self.strum_chords[x]

            notes = self.strum.notes[1]
            self.chord = [x + self.strum.pitch for x in notes]
            self.strum_notes = utils.pad_intervals(len(self.chord))
            # light on pads
            pads = self.ordered[: len(self.strum_chords)]
            mp.group_light_on(pads)
            # blink active
            mp.light_blink(self.ordered[x])
        except:
            pass

    def handle_pad(self, sysEx):
        self.load_strum(self.ordered[sysEx.control])

    def handle_rotary(self, sysEx):
        pass

    # if sysEx.data == 1:
    #     self.strum_chords.rotate(-1)
    # else:
    #     self.strum_chords.rotate(1)
    # self.load_strum()

    def handle_button(self, sysEx):
        if sysEx.control == pk.BUTTON_PAD:
            pass
            # self.handle_xy_pad(sysEx)

    def handle_xy_pad(self, sysEx):
        """x/y pad during fast sliding does not always return precise values,
        tolerance value from `math.isclose` reduce sensitivity of receiving values,
        custom strum_queue removes duplicate values within tolerance range

        Caution: for slower tempos keep tolerance value small to send midi
        as fast as sysex value leaves strum range, for higher tempos it is recommended
        to increate tolerance value to catch x/y pad data
        """
        alist = [isclose(sysEx.data[0], x, abs_tol=2) for x in self.strum_notes]
        # check, if value is in range of any strum
        if any(alist):
            # find index of triggered strum
            idx = alist.index(True)
            # add strum pitch and velocity of first occurence and handle any duplicates in same range
            self.strum_queue.put_nowait(Strum(self.chord[idx], sysEx.data[1]))
        else:
            # send strum in midi
            self.send_strum()

    def send_strum(self):
        """Send strum values as midi
        """
        while not self.strum_queue.empty():
            try:
                strum = self.strum_queue.get_nowait()
                mp.send_midi(
                    dict(
                        type="note_on",
                        note=strum.pitch,
                        velocity=strum.velocity,
                        channel=self.channel,
                    )
                )
                # mp.send_midi(
                #     dict(type="note_off", note=note, velocity=0, channel=self.channel)
                # )
            except:
                pass
