import socket
import time
import json

from packet_fields import PacketFields
from packet_types import PacketTypes

SEQ_ERROR_NUM = 99999
ACK_ERROR_BUFFER_FRAME = 2
TIMEOUT_ERROR_BUFFER_FRAME = 8

class Server:
    def __init__(self, port=10000, address='localhost', window=5) -> None:
        self.window = 5
        self.port = port
        self.address = address

        self.buffer = []
        self.next_ack_expecting = 0

        self._exit_flag = False

        # NOTE: We need to set a few more variables in order to introduce
        #       artificial errors requested in the project description.
        self.need_to_show_ack_error = True
        self.need_to_show_timeout_error = True
        self.ack_packet_error_number = ACK_ERROR_BUFFER_FRAME
        self.timeout_error_number = TIMEOUT_ERROR_BUFFER_FRAME

    def run(self) -> None:
        server_address = (self.address, self.port)
        print(f"\nStarting up on {self.address} port {self.port}\n")

        try:
            # NOTE: This socket will stay blocking as the protocol calls for a
            #       synchronous server.
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind(server_address)
        except socket.error as error:
            print('Error binding socket.', error)

        while not self._exit_flag:
            data, address = sock.recvfrom(4096)
            print(f"\nreceived {len(data)} bytes from {address}\n")
            print(f"Expected: {self.next_ack_expecting}")
            print(f"{data}")

            decoded_data = self._decode(data)

            if not data:
                continue

            response = self._handle_packet(decoded_data)
            response = self._introduce_error(response)

            if not response:
                continue            

            sent = sock.sendto(self._encode(response), address)

            print(f"\nsending ack for {response}")
            print(f"sent {sent} bytes back to {address}\n")

    def _encode(self, data) -> bytearray:
        data_as_json = json.dumps(data)
        return data_as_json.encode()

    def _decode(self, packet) -> json:
        try:
            decoded_packet = packet.decode()
            return json.loads(decoded_packet)
        except UnicodeDecodeError as error:
            print('Failed to decode a packet.', error)
        except json.JSONDecodeError as error:
            print('Unable to parse packet to JSON.', error)

    def _handle_packet(self, packet_data) -> json:
        packet_type = packet_data[self._as_string_key(PacketFields.TYPE)]

        response = None

        if packet_type == PacketTypes.START:
            response = self._handle_start_packet()
        elif packet_type == PacketTypes.DATA:
            response = self._handle_data_packet(packet_data)
        elif packet_type == PacketTypes.STOP:
            response = self._handle_stop_packet(packet_data)

        return response

    def _handle_start_packet(self) -> json:
        self._reset()
        self.next_ack_expecting += 1
        return self._build_ack_response(0)

    def _handle_stop_packet(self, packet) -> json:
        ack_number = int(packet[self._as_string_key(PacketFields.SEQUENCE_NUMBER)])
        self._dump_buffer_to_file()
        self._exit_flag = True
        return self._build_ack_response(ack_number)

    def _handle_data_packet(self, packet) -> json:
        ack_number = int(packet[self._as_string_key(PacketFields.SEQUENCE_NUMBER)])

        # NOTE: If we receive a packet sequence number we are not expecting it is discarded and not
        #       added to our receive buffer.
        if self.next_ack_expecting == ack_number:
            print(f"\nAdding data to buffer from frame: {self.next_ack_expecting}\n")
            print(f"current buffer: {self.buffer}")
            self.buffer.append(packet[self._as_string_key(PacketFields.DATA)])
            self.next_ack_expecting += 1

        return self._build_ack_response(self.next_ack_expecting - 1)

    def _build_ack_response(self, ack_number) -> json:
        return {
            PacketFields.TYPE: PacketTypes.ACK,
            PacketFields.SEQUENCE_NUMBER: ack_number
        }

    def _reset(self) -> None:

        self.buffer = []
        self.next_ack_expecting = 0

        # NOTE: The error flags need to be reset if we want to see artificial error on a
        #       client retransmit without manually restarting the server.
        self.need_to_show_ack_error = True
        self.need_to_show_timeout_error = True

    def _dump_buffer_to_file(self) -> None:
        with open('receive.txt', 'w+', encoding='UTF-8') as received_file:
            for frame in self.buffer:
                received_file.write(f"{frame.capitalize()}\n")

    def _as_string_key(self, val) -> str:
        return str(int(val))

    def _introduce_error(self, response) -> json:
        error_type = response[PacketFields.SEQUENCE_NUMBER]

        if self.need_to_show_ack_error and error_type == self.ack_packet_error_number:
            self.need_to_show_ack_error = False
            print('\nIntroducing ACK error.\n')
            response[PacketFields.SEQUENCE_NUMBER] = SEQ_ERROR_NUM
        elif self.need_to_show_timeout_error and error_type == self.timeout_error_number:
            self.need_to_show_timeout_error = False
            print('\nIntroducing timeout error.\n')
            time.sleep(3)
            response = None

        return response

if __name__ == "__main__":
    server = Server()
    server.run()
