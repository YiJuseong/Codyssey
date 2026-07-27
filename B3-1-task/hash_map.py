from doubly_linked_list import DoublyLinkedList, Node

class HashEntry:
    """해시맵 체이닝에 사용될 엔트리 구조체"""
    def __init__(self, key, value, lru_node: Node):
        self.key = key
        self.value = value
        self.lru_node = lru_node  # LRU 노드 참조 포인터
        self.expire_at = None     # 만료 시각 (타임스탬프, None이면 무제한)


class HashMap:
    """체이닝 방식 및 동적 확장을 지원하는 커스텀 해시맵"""
    def __init__(self, initial_capacity=16):
        self.capacity = initial_capacity
        # 각 버킷은 충돌 해결을 위해 이중 연결 리스트(DoublyLinkedList)로 초기화
        self.buckets = [DoublyLinkedList() for _ in range(self.capacity)]
        self._size = 0

    def _hash(self, key: str) -> int:
        """문자열 키에 대한 해시 값을 직접 계산 (DJB2 알고리즘 응용)"""
        h = 5381
        for char in key:
            h = ((h << 5) + h) + ord(char)
        return h & 0x7FFFFFFF

    def size(self):
        return self._size

    def _resize(self):
        """버킷 크기를 2배로 확장하고 재해싱"""
        old_buckets = self.buckets
        self.capacity *= 2
        self.buckets = [DoublyLinkedList() for _ in range(self.capacity)]
        self._size = 0

        for blist in old_buckets:
            curr = blist.head.next
            while curr != blist.tail:
                # curr.value에 HashEntry 객체가 들어있음
                entry = curr.value
                self.put_entry(entry.key, entry)
                curr = curr.next

    def put_entry(self, key: str, entry: HashEntry):
        """내부용: 재해싱 등을 위해 Entry 객체를 직접 삽입"""
        idx = self._hash(key) % self.capacity
        blist = self.buckets[idx]
        
        # 이미 존재하는지 확인
        curr = blist.head.next
        while curr != blist.tail:
            if curr.key == key:
                curr.value = entry
                return
            curr = curr.next
        
        # 신규 삽입
        new_node = Node(key, entry)
        blist.insert_back(new_node)
        self._size += 1

    def put(self, key: str, value, lru_node: Node) -> HashEntry:
        """키-값 쌍을 해시맵에 저장"""
        if self._size / self.capacity > 0.75:
            self._resize()

        idx = self._hash(key) % self.capacity
        blist = self.buckets[idx]
        
        curr = blist.head.next
        while curr != blist.tail:
            if curr.key == key:
                entry = curr.value
                entry.value = value
                entry.lru_node = lru_node
                return entry
            curr = curr.next

        # 존재하지 않으면 새로 생성
        entry = HashEntry(key, value, lru_node)
        new_node = Node(key, entry)
        blist.insert_back(new_node)
        self._size += 1
        return entry

    def get(self, key: str) -> HashEntry:
        """키에 해당하는 HashEntry 객체를 반환 (없으면 None)"""
        idx = self._hash(key) % self.capacity
        blist = self.buckets[idx]
        
        curr = blist.head.next
        while curr != blist.tail:
            if curr.key == key:
                return curr.value
            curr = curr.next
        return None

    def remove(self, key: str) -> bool:
        """키 삭제 성공 시 True, 없으면 False 반환"""
        idx = self._hash(key) % self.capacity
        blist = self.buckets[idx]
        
        curr = blist.head.next
        while curr != blist.tail:
            if curr.key == key:
                blist.remove_node(curr)
                self._size -= 1
                return True
            curr = curr.next
        return False

    def contains(self, key: str) -> bool:
        return self.get(key) is not None

    def keys(self) -> list:
        """순서 없는 전체 키의 파이썬 리스트 반환 (출력용)"""
        res = []
        for blist in self.buckets:
            curr = blist.head.next
            while curr != blist.tail:
                res.append(curr.key)
                curr = curr.next
        return res