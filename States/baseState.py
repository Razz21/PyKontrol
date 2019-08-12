import padKontrol as pk
import mido
import time
import operator
from functools import wraps
import midi_ports as mp


class StateBase:
    """Base object for concrete configuration states.

    Global variables:
        state_name -- state specyfic name displayed on led.
        _KNOBS -- knobs sysEx description.
        _RESERVED_CONTROLLERS -- controllers for global actions.
        _context -- context object reference.
        _GLOBAL_COMBINATIONS -- global hotkeys combinations dictionary:
            key: controls combination, value: called function name (string).
    """

    state_name = "base"
    _KNOBS = [pk.ROTARY_KNOB, pk.KNOB_1, pk.KNOB_2]
    _RESERVED_CONTROLLERS = [pk.BUTTON_KNOB_1_ASSIGN, pk.BUTTON_KNOB_2_ASSIGN]
    _context = None
    _GLOBAL_COMBINATIONS = {
        frozenset([pk.BUTTON_SETTING, pk.ROTARY_KNOB]): "change_state"
    }

    def __init__(self):
        self.hotkeys = set()
        self._LOCAL_COMBINATIONS = {}

    def __str__(self):
        return self.name

    def hotkey_method(self, sysEx):
        print("hotkey found!!")

    def load_state(self):
        """
        Generic initialization method for context object handler
        """
        pass

    def change_state(self, sysEx) -> None:
        """Change state trigger for context object

        Arguments:
            sysEx message

        Returns:
            None -- load new state
        """
        self._pause()
        # todo reset all lights
        # mp.send_sysex(
        #     pk.light_group('ABC', dict.fromkeys(pk.ALL_PADS, False))
        # )
        mp.group_light_off(pk.ALL_BUTTONS)
        mp.group_light_off(pk.ALL_PADS)
        if sysEx.data == 1:
            self._context.next_state()
        else:
            self._context.previous_state()

    # ------------------------handle events ---------------------------

    def handle_default_action(self, sysEx):
        """Handle pre-defined global actions
        
        Arguments:
        sysEx {SysexEvent} -- sysEx message from PK controller
        """
        pass

    def catch_combination(self, sysEx):
        """Catch combo or fire default global action for reserved knobs/buttons.
        Check action flow:
        global combination -> default global action -> modes actions

        Arguments:
            sysEx {SysexEvent} -- sysEx message from PK controller

        Returns:
            bool -- global or local hotkey combo found
        """

        catched = False

        if sysEx.state in (pk.NOTE_ON, 1):
            # catch combination if button pressed or knob turned
            self.hotkeys.add(sysEx.control)
            if frozenset(self.hotkeys) in self._GLOBAL_COMBINATIONS:
                combo_method = self._GLOBAL_COMBINATIONS[frozenset(self.hotkeys)]
                #  find and call method in class scope
                operator.attrgetter(combo_method)(self)(sysEx)
                catched = True

            elif frozenset(self.hotkeys) in self._LOCAL_COMBINATIONS:
                self._LOCAL_COMBINATIONS[frozenset(self.hotkeys)](sysEx)
                catched = True
            else:
                self.handle_default_action(sysEx)
        else:
            # remove from hotkeys queue on release
            self.hotkeys.discard(sysEx.control)

        # knobs do not send on/off state,
        # controller must be removed from hotkey queue every turn
        if sysEx.control in self._KNOBS:
            self.hotkeys.discard(sysEx.control)

        return catched

    def handle_event(self, sysEx):
        """Base event handler for State Object.

        Catch global events / controller combinations:
        - change mode,
        - transpose notes,  #TODO
        - etc.              #TODO
        or dispatch to state specyfic handler.

        Arguments:
            sysEx {SysexEvent} -- sysEx message from PK controller
        """

        # global events take prevedence over state actions or combinations
        if sysEx.control in self._RESERVED_CONTROLLERS:
            self.handle_default_action(sysEx)

        # catch controllers combination
        elif self.catch_combination(sysEx):
            return

        # pass signal to active state handler
        else:
            self.handle_state_event(sysEx)

    def handle_state_event(self, sysEx):
        """State specyfic sysEx event handler

        Arguments:
            sysEx {SysexEvent} -- sysEx message from PK controller
        """
        method = getattr(self, "handle_%s" % sysEx.type)
        method(sysEx)

    def handle_pad(self, sysEx):
        pass

    def handle_button(self, sysEx):
        pass

    def handle_rotary(self, sysEx):
        pass

    def handle_knob(self, sysEx):
        pass

    def handle_xy_pad(self, sysEx):
        pass

    # ------------------------ state runtime methods --------------------------

    def _start(self, data=None):
        """
        Load configuration specyfic initialization methods.
        Should be used in threading-driven configuration
        to call threading's .start() method
        """
        pass

    def _pause(self, data=None):
        """
        Handle threading-driven configuration method.
        Should be overriden to stop current configuration`s thread on state change
        """
        pass
