from enum import IntEnum

class PacketFields(IntEnum):
    TYPE = 1,
    DATA = 2,
    SEQUENCE_LENGTH = 3,
    SEQUENCE_NUMBER = 4,
