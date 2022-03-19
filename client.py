import socket
import select
import time
import json

from packet_fields import PacketFields
from packet_types import PacketTypes

class Client:
    def __init__(self, window=5, timeout=2, max_timeouts=3, port=10000, address='localhost') -> None:
        self._pending_ack = 0
        self._to_send = 0
        self._window = window
        self._timeout_after_seconds = timeout

        self._address = address
        self._port = port
        self._server_address = (self._address, self._port)

        self._buffer = []
        self._sock = None

        self._consecutive_timeouts_maximum = max_timeouts
        self._consecutive_timeouts = 0

    def transmit(self) -> None:
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # NOTE: The socket can be non-blocking since we are monitoring system events manually.
        self._sock.setblocking(0)

        # NOTE: epoll is a utility for monitoring OS events. The code as is
        #       will not run on a windows environment, or any other environment
        #       that does not support epoll.
        epoll = select.epoll()
        epoll.register(self._sock.fileno(), select.EPOLLIN)

        while True:
            if len(self._buffer) <= self._pending_ack:
                print('Stopping transmit, closing socket.')
                self._sock.close()
                return

            try:
                # NOTE: We don't send on EPOLLOUT because we have a custom defined
                #       buffer/buffer frames for easy visualization and project requirements.
                self._send()

                events = epoll.poll(timeout=self._timeout_after_seconds)

                # NOTE: Since events is a list, a [] indicates no event on the sockets file
                #       descriptor inside of the timeout window
                if not events:
                    raise TimeoutError()

                for _, event in events:
                    if event & select.EPOLLIN:
                        self._receive()

            except TimeoutError:
                print('Timeout detected, triggering retransmit of window.')
                self._consecutive_timeouts += 1

                if self._consecutive_timeouts >= self._consecutive_timeouts_maximum:
                    print('Maximum consecutive timeouts occurred. Ending transmission.')
                    return

                # NOTE: Moving the transmit window buffer frame pointers here is what triggers
                #       the retransmit of the window.
                self._to_send = self._pending_ack

    def populate_transmission_buffer(self) -> None:
        data = self._read_file()

        buffer = [self._build_start_packet()]

        for i, frame in enumerate(data):
            buffer.append(self._build_transmission_packet(i+1, frame))

        self._buffer = buffer + [self._build_stop_packet(len(data)+1)]

    def _send(self) -> None:
        while self._to_send < len(self._buffer) and self._to_send - self._pending_ack < self._window:

            # NOTE: This .sendto could EAGAIN or EWOULDBLOCK but its essentially prevented
            #       with the custom defined buffer and buffer frames, so we won't catch the 
            #       EnvironmentError that would be raised.
            _ = self._sock.sendto(self._encode(self._buffer[self._to_send]), self._server_address)

            print(f"\nSent: {self._buffer[self._to_send]}")
            print(f"Timestamping at {time.time()}\n")

            self._to_send += 1

    def _receive(self) -> None:
        data, _ = self._sock.recvfrom(4096)
        received_packet = self._decode(data)

        # NOTE: the guard clause covers the potentially null socket read
        if data:
            self._consecutive_timeouts = 0
            current_ack = int(received_packet[str(int(PacketFields.SEQUENCE_NUMBER))])

            print(f"\nLooking for ACK for {self._pending_ack}")
            print(f"received_packet: {received_packet}")
            print(f"Sequence Number: {current_ack}")

            if current_ack > self._pending_ack:
                print(f"\nACK sequencing error detected. Resending frame starting at {self._pending_ack}.\n")
                self._to_send = self._pending_ack
            else:
                self._pending_ack = current_ack + 1

    def _encode(self, data) -> bytearray:
        data_as_json = json.dumps(data)
        return data_as_json.encode()

    def _decode(self, data):
        decoded_packet = data.decode()
        return json.loads(decoded_packet)

    def _read_file(self) -> list:
        names = None
        with open('transmit.txt', 'r', encoding='UTF-8') as input_file:
            names = input_file.readlines()

        return [name.strip() for name in names]

    def _build_start_packet(self) -> json:
        return {
            PacketFields.TYPE: PacketTypes.START,
            PacketFields.SEQUENCE_NUMBER: 0,
        }

    def _build_stop_packet(self, sequence_number) -> json:
        return {
            PacketFields.TYPE: PacketTypes.STOP,
            PacketFields.SEQUENCE_NUMBER: sequence_number
        }

    def _build_transmission_packet(self, sequence_number, data) -> json:
        return {
            PacketFields.TYPE: PacketTypes.DATA,
            PacketFields.SEQUENCE_NUMBER: sequence_number,
            PacketFields.DATA: data
        }

if __name__ == '__main__':
    client = Client()
    client.populate_transmission_buffer()
    client.transmit()
