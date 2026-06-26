class Node:
    """이중 연결 리스트의 노드 클래스"""
    def __init__(self, key=None, value=None):
        self.key = key
        self.value = value
        self.prev = None
        self.next = None


class DoublyLinkedList:
    """LRU 관리를 위한 이중 연결 리스트 구현 (더미 헤드/테일 사용)"""
    def __init__(self):
        self.head = Node()  # 가장 최근에 사용됨 (Front)
        self.tail = Node()  # 가장 오래전에 사용됨 (Back)
        self.head.next = self.tail
        self.tail.prev = self.head
        self._size = 0

    def size(self):
        return self._size

    def insert_front(self, node: Node):
        """노드를 리스트의 맨 앞(head 뒤)에 삽입"""
        first = self.head.next
        self.head.next = node
        node.prev = self.head
        node.next = first
        first.prev = node
        self._size += 1

    def insert_back(self, node: Node):
        """노드를 리스트의 맨 뒤(tail 앞)에 삽입"""
        last = self.tail.prev
        last.next = node
        node.prev = last
        node.next = self.tail
        self.tail.prev = node
        self._size += 1

    def remove_node(self, node: Node):
        """지정된 노드를 리스트에서 제거"""
        if node.prev and node.next:
            node.prev.next = node.next
            node.next.prev = node.prev
            node.prev = None
            node.next = None
            self._size -= 1

    def remove_front(self) -> Node:
        """맨 앞의 노드를 제거하고 반환"""
        if self._size == 0:
            return None
        node = self.head.next
        self.remove_node(node)
        return node

    def remove_back(self) -> Node:
        """맨 뒤의 노드(LRU 타겟)를 제거하고 반환"""
        if self._size == 0:
            return None
        node = self.tail.prev
        self.remove_node(node)
        return node

    def move_to_front(self, node: Node):
        """기존 노드를 맨 앞으로 이동 (O(1))"""
        self.remove_node(node)
        self.insert_front(node)