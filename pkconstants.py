
# button constants
BUTTON_SCENE = 0x10
BUTTON_MESSAGE = 0x11
BUTTON_SETTING = 0x12
BUTTON_NOTE_CC = 0x13
BUTTON_MIDI_CH = 0x14
BUTTON_SW_TYPE = 0x15
BUTTON_REL_VAL = 0x16
BUTTON_VELOCITY = 0x17
BUTTON_PORT = 0x18
BUTTON_FIXED_VELOCITY = 0x19
BUTTON_PROG_CHANGE = 0x1A
BUTTON_X = 0x1B
BUTTON_Y = 0x1C
BUTTON_KNOB_1_ASSIGN = 0x1D
BUTTON_KNOB_2_ASSIGN = 0x1E
BUTTON_PEDAL = 0x1F
BUTTON_ROLL = 0x20
BUTTON_FLAM = 0x21
BUTTON_HOLD = 0x22
BUTTON_PAD = 0X30

# light state constants
LIGHT_STATE_OFF = 0x00
LIGHT_STATE_ON = 0x20
LIGHT_STATE_ONESHOT = 0x40
LIGHT_STATE_BLINK = 0x60

# LED state constants
LED_STATE_ON = 0x00
LED_STATE_BLINK = 0x01

# SYSEX constants
_SYSEX_COMMON = [0xF0, 0x42, 0x40, 0x6E, 0x08]
SYSEX_NATIVE_MODE_ON = _SYSEX_COMMON + [0x00, 0x00, 0x01, 0xF7]
SYSEX_NATIVE_MODE_ENABLE_OUTPUT = _SYSEX_COMMON + [
    0x3F, 0x2A, 0x00, 0x00, 0x05, 0x05, 0x05, 0x7F, 0x7E, 0x7F, 0x7F, 0x03,
    0x0A, 0x0A, 0x0A, 0x0A, 0x0A, 0x0A, 0x0A, 0x0A, 0x0A, 0x0A, 0x0A, 0x0A, 0x0A, 0x0A, 0x0A, 0x0A, 
    0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 
    0x0A, 0x0B, 0x0C, 0x0d, 0x0E, 0x0F, 0x10, 0xF7
    ]
SYSEX_NATIVE_MODE_INIT = _SYSEX_COMMON + [
    0xF0, 0x42, 0x40, 0x6E, 0x08, 0x3F, 0x0A, 0x01,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x29, 0x29, 0x29, 0xF7
    ]
# displays YES on LED if native mode is enabled properly
SYSEX_NATIVE_MODE_TEST = _SYSEX_COMMON + [0x22, 0x04, 0x00, 0x59, 0x45, 0x53, 0xF7]

SYSEX_NATIVE_MODE_OFF = _SYSEX_COMMON + [0x00, 0x00, 0x00, 0xF7]
