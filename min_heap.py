class MinHeap:
    """TTL 관리를 위한 (expire_at, key) 쌍 저장용 최소 힙"""
    def __init__(self):
        self.heap = []  # 파이썬 기본 list를 가변 배열 크기로 사용 (인덱스 접근 전용)

    def size(self):
        return len(self.heap)

    def peek(self):
        if len(self.heap) == 0:
            return None
        return self.heap[0]

    def push(self, element: tuple):
        """element는 (expire_at, key) 형태의 튜플"""
        self.heap.append(element)
        self._heapify_up(len(self.heap) - 1)

    def pop(self) -> tuple:
        if len(self.heap) == 0:
            return None
        if len(self.heap) == 1:
            return self.heap.pop()
        
        root = self.heap[0]
        self.heap[0] = self.heap.pop()
        self._heapify_down(0)
        return root

    def _heapify_up(self, idx: int):
        parent = (idx - 1) // 2
        while idx > 0 and self.heap[idx][0] < self.heap[parent][0]:
            self.heap[idx], self.heap[parent] = self.heap[parent], self.heap[idx]
            idx = parent
            parent = (idx - 1) // 2

    def _heapify_down(self, idx: int):
        n = len(self.heap)
        smallest = idx
        while True:
            left = 2 * idx + 1
            right = 2 * idx + 2
            
            if left < n and self.heap[left][0] < self.heap[smallest][0]:
                smallest = left
            if right < n and self.heap[right][0] < self.heap[smallest][0]:
                smallest = right
                
            if smallest != idx:
                self.heap[idx], self.heap[smallest] = self.heap[smallest], self.heap[idx]
                idx = smallest
            else:
                break