from enum import Enum

class Direction(Enum):
    LONG = "long"
    SHORT = "short"
    EXIT = "exit"

class Signal:
    def __init__(self, name: str, direction: Direction, score: float):
        self.name = name
        self.direction = direction
        self.score = score
