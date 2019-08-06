import mido


PADKONTROL_OUTPUT_PORT = "padKONTROL 1 CTRL 2"
PADKONTROL_INPUT_PORT = "padKONTROL 1 PORT A 1"

OUTPUT_MIDI_PORT = "padKONTROL 1 CTRL 2"
INPUT_MIDI_PORT = "padKONTROL 1 PORT A 1"
DATA_MIDI_PORT = "KorgLoopMidi 5"


_midi_in = None
_midi_out = None
_midi_out_data = None


def get_midi_in():
    global _midi_in
    if not _midi_in:
        _midi_in = mido.open_input(PADKONTROL_INPUT_PORT)
    return _midi_in


def get_midi_out():
    global _midi_out
    if not _midi_out:
        _midi_out = mido.open_output(PADKONTROL_OUTPUT_PORT)
    return _midi_out


def get_midi_out_data():
    global _midi_out_data
    if not _midi_out_data:
        _midi_out_data = mido.open_output(DATA_MIDI_PORT)
    return _midi_out_data


def get_midi_ports():
    midi_in = get_midi_in()
    midi_out = get_midi_out()
    midi_out_data = get_midi_out_data()
    return midi_in, midi_out, midi_out_data


def get_padkontrol_input():
    return get_midi_in()


def get_padkontrol_output():
    return get_midi_out()


def get_input_to_host():
    return get_midi_out_data()


def get_input_from_host():
    return get_midi_out_data()
