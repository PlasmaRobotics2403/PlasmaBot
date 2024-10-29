from enum import Enum, auto


class BotState(Enum):
    OFFLINE = auto()
    STARTING = auto()
    READY = auto()
    SHUTDOWN = auto()
    RESTART = auto()

current_state = BotState.OFFLINE

def update_state(new_state):
    global current_state
    current_state = new_state


def get_state():
    global current_state
    return current_state


class FatalException(Exception):
    """An Exception Thrown when an error would prevent normal operation
        and cannot be automatically resolved"""
    
    def __init__(self,title,message):
        self._title = title
        self._message = message

        super().__init__(self, 'Fatal Error Encountered: {}'.format(message))

    def title(self):
        return self._title

    def message(self):
        return self._message