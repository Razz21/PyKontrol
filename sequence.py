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
      - switch between stages
    """

    __instances = {}
    __limit = 16

    def __init__(self, channel: int, *args, **kwargs):
        self._channel = channel
        self.max_steps = 16
        self.active_steps = set()  # maybe dict with object

    def __str__(self):
        return f"stage {self.channel}"

    def __new__(cls, channel: int, *args, **kwargs):
        if len(cls.__instances) > cls.__limit:
            raise ValueError(f"Count not create instance. Limit {cls.__limit} reached")
        if channel < 1 or channel > cls.__limit:
            raise ValueError(
                f"Count not create instance. Channel must be in range 1-{cls.__limit}"
            )

        obj = cls.__instances.get(channel, None)
        if obj:
            # copy __init__ with params
            cls.__init__ = new_init(cls, cls.__init__)
        else:
            # create new instance
            cls.__instances[channel] = object.__new__(cls)

        return cls.__instances[channel]

    @classmethod
    def get(cls, value):
        return [inst for inst in cls.instances if inst.channel == value]

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
    stages = {}

    def __init__(self, *args, **kwargs):
        self.channel = 1

    def get_stage_or_create(self, channel):
        current_stage = self.stages.get(channel, None)
        if not current_stage:
            current_stage = Stage(channel)
            self.stages[channel] = current_stage
        return current_stage


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
