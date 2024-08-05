import queue
import math
import random

import numpy as np
from abc import ABC
from time import sleep

from src.packets.packets import Batch, batch_to_packets, Packet, Buffer, packets_to_batch


class Node(ABC):
    def __init__(self, node_id, network_id, packet_size, gf, network):
        self.node_id = node_id
        self.network_id = network_id
        self.packet_size = packet_size
        self.gf = gf
        self.network = network
        self.next_node: Node | None = None
        self.buffer = None
        self.max_buffer_length = None

    def transmission(self, packets: list[Packet]):
        if self.next_node:
            for packet in packets:
                self.network.transmissions[self.next_node.node_id].put(packet)

    def listen(self):
        item = self.network.transmissions[self.node_id].get()
        # print(f"id: {self.node_id} receiving item: {item.batch_id}")
        self.network.transmissions[self.node_id].task_done()
        if self.buffer.qsize() < self.max_buffer_length:
            packet_list = self.buffer.put(item)
            if packet_list is not None:
                # print(f"packet id {self.node_id} transmissing {packet_list[0].batch_id}")
                return self.simple_recode(packet_list)
        return None

    def add_next_node(self, next_node_):
        self.next_node = next_node_

    def create_batch_from_file(self, file, file_size) -> Batch:
        pass

    def run(self, file=None, file_size=None):
        while True:
            if isinstance(self, (DestinationNode, IntermediateNode)):
                res = self.listen()
                if res is not None and isinstance(self, IntermediateNode):
                    self.transmission(res)
            else:
                batch = self.create_batch_from_file(file, file_size)
                self.transmission(batch_to_packets(batch, self.gf))
            sleep(1)

    def simple_recode(self, packets: list[Packet]):
        number_of_packets: int = len(packets)
        batch_id: int = packets[0].batch_id
        batch_size: int = Batch.batch_mapping[packets[0].batch_id].shape[1]
        linear_combination_coeff_matrix = self.gf.Random((number_of_packets, batch_size))

        new_packets: list[Packet] = []
        for j in range(batch_size):
            new_coeff_vector = self.gf([0 for _ in range(len(packets[0].coeff_vector))])
            new_payload_vector = self.gf([0 for _ in range(self.packet_size)])
            for i in range(number_of_packets):
                new_coeff_vector += linear_combination_coeff_matrix[i][j] * packets[i].coeff_vector
                new_payload_vector += linear_combination_coeff_matrix[i][j] * packets[i].payload

            new_packets.append(Packet(batch_id, new_payload_vector, self.gf, new_coeff_vector))

        # print("linear_combination_coeff:\n", linear_combination_coeff_matrix)
        # print("coeff:\n", coeff_matrix)
        # print("payload:\n", payload_matrix)

        # print("new_coeff_matrix:\n", new_coeff_matrix)
        # print("new_payload_matrix:\n", new_payload_matrix)
        return new_packets


class SourceNode(Node):
    def __init__(self, node_id, network_id, max_degree, packet_size, gf, network):
        super().__init__(node_id, network_id, packet_size, gf, network)
        self.max_degree: int = max_degree

    def create_batch_from_file(self, file, file_size) -> Batch:
        number_of_packets = math.ceil(file_size / self.packet_size)
        degree = random.randint(1, self.max_degree)
        batch = []
        for i in range(degree):
            position_in_bytes = random.randint(0, number_of_packets - 1) * self.packet_size
            file.seek(position_in_bytes)
            packet = []
            for j in range(self.packet_size):
                packet.append(int.from_bytes(file.read(1), byteorder="big"))  # field size = 256
            batch.append(self.gf(packet))
        batch = self.gf(np.transpose(batch))

        generator_matrix = self.gf.Random((degree, degree))  # size not confirm

        return Batch(batch @ generator_matrix, generator_matrix, None)


class IntermediateNode(Node):
    def __init__(self, node_id, network_id, packet_size, gf, network, max_buffer_length=100):
        super().__init__(node_id, network_id, packet_size, gf, network)
        self.buffer: Buffer = Buffer()
        self.max_buffer_length = max_buffer_length


class DestinationNode(Node):
    def __init__(self, node_id, network_id, packet_size, gf, network, max_buffer_length=100):
        super().__init__(node_id, network_id, packet_size, gf, network)
        self.buffer: Buffer = Buffer()
        self.max_buffer_length = max_buffer_length

    def decode(self):
        pass


if __name__ == "__main__":
    SourceNode()
