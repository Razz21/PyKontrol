class Step:
    def __init__(self, *args, **kwargs):
        self.velocity = 127


def new_init(cls, init):
    # https://stackoverflow.com/a/45268946/10922608
    def reset_init(*args, **kwargs):
        cls.__init__ = init

    return reset_init


class Stage:
    """
    Stage class for available channels 1-16
    attributes:
      - specify independent steps
    
    """

    def __init__(self, channel: int, *args, **kwargs):
        self._channel = channel
        self.max_steps = 16
        self.active_steps = set()  # maybe dict with object

    def __str__(self):
        return f"stage {self.channel}"

    @property
    def channel(self):
        return self._channel

    @channel.setter
    def channel(self, value: int) -> None:
        if not isinstance(value, int):
            raise TypeError("Channel must be an int")
        self._channel = value

    def add_steps(self, step: int) -> None:
        self.active_steps.add(step)

    def remove_step(self, step: int) -> None:
        self.active_steps.discard(step)  # not throw error


class Sequencer:
    """
    Stage class for available channels 1-16
    attributes:
      - store used stages
      - switch between stages
    """

    stages = {}

    def __init__(self, *args, **kwargs):
        self.port = 1
        self.max_stages = 4
        self.stage = None

    def get_stage_or_create(self, port):
        current_stage = self.stages.get(port, None)
        if not current_stage:
            current_stage = Stage(port)
            self.stages[port] = current_stage
            self.stage = current_stage
        return current_stage

    def get_stage(self):
        return self.stage

    def save_stage(self):
        self.stages[self.port] = self.stage

    def clean_stage(self):
        self.stages[self.port] = Stage(self.port)


# seq = Sequencer()

# stage1 = seq.get_stage_or_create(1)

# print(stage1.active_steps)
# stage1.add_steps(1)
# stage1.add_steps(12)
# print(stage1.active_steps)
# print(stage1)


# s2 = seq.get_stage_or_create(1)
# s2.remove_step(12)
# print(stage1 == s2)
# print(stage1.active_steps)
