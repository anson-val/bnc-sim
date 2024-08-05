import galois
from queue import Queue


class Buffer(Queue):
    def __init__(self):
        self.current_batch_id = None
        super().__init__()

    def put(self, packet, block=True, timeout=None) -> list | None:
        packets = None
        if self.current_batch_id is None:
            self.current_batch_id = packet.batch_id
        elif self.current_batch_id != packet.batch_id:
            self.current_batch_id = packet.batch_id
            packets = self.get(block, timeout)
        super().put(packet, block, timeout)
        return packets

    def get(self, block=True, timeout=None) -> list:
        packets = []
        while not self.empty():
            packets.append(super().get(block, timeout))
            super().task_done()
        return packets


class Batch:
    next_batch_id = 0

    batch_mapping: dict = {}

    def __init__(self, batch, generator_matrix, original_id: None | int):
        self.batch = batch
        self.generator = generator_matrix
        if original_id is not None:
            self.batch_id = original_id
        else:
            Batch.batch_mapping[Batch.next_batch_id] = generator_matrix
            self.batch_id = Batch.next_batch_id
            Batch.next_batch_id += 1
        print("batch id:", self.batch_id, "degree:", self.batch.shape[1])


class Packet:
    def __init__(self, batch_id, packet_content, field, coeff_vector):
        self.batch_id = batch_id
        self.payload = packet_content
        self.field = field
        self.coeff_vector = coeff_vector

    def __str__(self):
        return f"{self.batch_id}: {self.payload}, {self.coeff_vector}"


def batch_to_packets(batch: Batch, field) -> list:
    num_of_columns = batch.batch.shape[1]
    packet_list = []
    for _ in range(num_of_columns):
        coeff_vector = [0 for _ in range(num_of_columns)]  # type: ignore
        coeff_vector[_] = 1
        packet_list.append(Packet(batch.batch_id, field(batch.batch[:, _]), field, field(coeff_vector)))
    return packet_list


def packets_to_batch(packets: list[Packet], field) -> Batch:
    batch = field([packet.payload for packet in packets])
    return Batch(batch, Batch.batch_mapping[packets[0].batch_id], packets[0].batch_id)
