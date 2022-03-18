from enum import IntEnum

class PacketTypes(IntEnum):
    START = 1,
    STOP = 2,
    DATA = 3,
    ACK = 4,
