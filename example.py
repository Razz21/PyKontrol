import time
import rtmidi

midiout = rtmidi.MidiOut()
available_ports = midiout.get_ports()

print(rtmidi.MidiIn().get_ports())
print(available_ports)

if available_ports:
    midiout.open_port(5)
else:
    midiout.open_virtual_port("My virtual output")
print(midiout.is_port_open())


note_on = [0x90, 60, 112] # channel 1, middle C, velocity 112
note_off = [0x80, 60, 0]
midiout.send_message([0x90, 60, 112])
time.sleep(0.5)
midiout.send_message([0x80, 60, 0])

del midiout

# midi_in = rtmidi.MidiIn()
# available_ports = midi_in.get_ports()

# print(available_ports)

# if available_ports:
#     midi_in.open_port(4)
# else:
#     midi_in.open_virtual_port("My virtual output")
# print(midi_in.is_port_open())

# note_on = [0x90, 60, 112] # channel 1, middle C, velocity 112
# note_off = [0x80, 60, 0]
# midi_in.send_message([0x90, 60, 112])
# time.sleep(0.5)
# midi_in.send_message([0x80, 60, 0])

# del midi_in