import padKontrol as pk
from midi_event import SysexEvent


class PadKontrolPrint(pk.PadKontrolInput):
    def __init__(self,):
        super().__init__()
        self._listener = None

    def on_pad_down(self, pad, velocity):
        # print("pad #%d down, velocity %d/127" % (pad, velocity))
        self.send_msg(SysexEvent("pad", pad, pk.NOTE_ON, velocity))

    def on_pad_up(self, pad):
        # print("pad #%d up" % pad)
        self.send_msg(SysexEvent("pad", pad, pk.NOTE_OFF, 0))

    def on_button_down(self, button):
        #  print("button #%d down" % button)
        self.send_msg(SysexEvent("button", button, 1))

    def on_button_up(self, button):
        #print("button #%d up" % button)
        self.send_msg(SysexEvent("button", button, 0))

    def on_knob(self, knob, value):
        # print("knob #%d value = %d" % (knob, value))
        self.send_msg(SysexEvent("knob", knob, 1, value))

    # def on_rotary_left(self):
    #     print("rotary turned left")
    #     self.send_msg(SysexEvent("rotary", pk.ROTARY_KNOB, 0))

    # def on_rotary_right(self):
    #     print("rotary turned right")
    #     self.send_msg(SysexEvent("rotary", pk.ROTARY_KNOB, 1))

    def on_rotary(self, val):
        # print("ON ROTARY", val)
        # val: left = 127, right = 1
        self.send_msg(SysexEvent("rotary", pk.ROTARY_KNOB, 1, val))

    def on_x_y(self, x, y):
        # print("x/y pad (x = %d, y = %d)" % (x, y))
        self.send_msg(SysexEvent("xy_pad", pk.BUTTON_PAD, 1, (x, y)))  # todo

    def register(self, listener):
        self._listener = listener

    def send_msg(self, msg):
        self._listener.notify(msg)

    def callback(self, message):
        # logging.info(message)
        sysex_buffer = []
        for byte in message.bytes():
            sysex_buffer.append(byte)
            if byte == 0xF7:
                self.process_sysex(sysex_buffer)
                del sysex_buffer[:]  # empty list
