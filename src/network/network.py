from enum import Enum

import galois
from src.nodes.nodes import Node, SourceNode, IntermediateNode, DestinationNode
from queue import Queue
import os
import threading
from src.packets.packets import Batch


class Network:
    next_network_id = 0

    def __init__(self, field_size, packet_size, max_degree):
        self.network_id: int = Network.next_network_id
        Network.next_network_id += 1
        self.packet_size = packet_size
        self.max_degree = max_degree
        self.tasks = []
        self.transmissions: dict[int, Queue] = {}
        self.gf = galois.GF(field_size)


class LineNetwork(Network):
    def __init__(self, field_size, number_of_nodes, packet_size, max_degree):
        super().__init__(field_size, packet_size, max_degree)
        self.number_of_nodes = number_of_nodes
        self.nodes: list[Node] = []
        self.threading = []
        self._build_network_graph()

    def _build_network_graph(self):
        self.source_node = SourceNode(0, self.network_id, self.max_degree, self.packet_size, self.gf, self)
        self.nodes.append(self.source_node)
        self.transmissions[0] = Queue()
        prev_node = self.source_node

        for i in range(self.number_of_nodes):
            current_node = IntermediateNode(i + 1, self.network_id, self.packet_size, self.gf, self)
            self.nodes.append(current_node)
            prev_node.add_next_node(current_node)
            prev_node = current_node
            self.transmissions[i + 1] = Queue()

        end_node = DestinationNode(self.number_of_nodes + 1, self.network_id, self.packet_size, self.gf, self)
        self.nodes.append(end_node)
        prev_node.add_next_node(end_node)
        self.transmissions[self.number_of_nodes + 1] = Queue()

    def feed_file(self, file_path):
        with open(file_path, "rb") as file:
            file_size = os.path.getsize(file_path)
            task = NetworkTask(NetworkTaskType.FILE, self.network_id)
            self.tasks.append(task)
            self.threading.append(threading.Thread(target=self.source_node.run, args=(file, file_size)))
            for node in self.nodes[1:-1]:
                self.threading.append(threading.Thread(target=node.run))
            self.threading.append(threading.Thread(target=self.nodes[-1].run))
            for thread in self.threading:
                thread.start()

        # file.close()


class NetworkTask:
    next_network_task_id = 0

    def __init__(self, task_type, network_id):
        self.network_task_id = NetworkTask.next_network_task_id
        NetworkTask.next_network_task_id += 1
        self.type: NetworkTaskType = task_type
        self.network_id = network_id
        self.is_received: bool = False
        self.batches: dict[int, Batch] = {}


class NetworkTaskType(Enum):
    FILE = 0
