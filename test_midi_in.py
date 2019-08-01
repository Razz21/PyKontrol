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
# print(midiout.is_port_open())


note_on = [0x90, 60, 112]  # channel 1, middle C, velocity 112
note_off = [0x80, 60, 0]
for _ in range(4):
    midiout.send_message([0x90, 60, 127])
    print("midi start")
    time.sleep(0.5)
    midiout.send_message([0x80, 60, 0])
    print("midi stop")
    time.sleep(.5)
del midiout


# time.sleep(0.01) # trigger time
