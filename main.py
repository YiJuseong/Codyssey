import time
import sys

from doubly_linked_list import DoublyLinkedList, Node
from hash_map import HashMap, HashEntry
from min_heap import MinHeap


class MiniRedis:
    def __init__(self):
        self.db = HashMap()
        self.lru_list = DoublyLinkedList()
        self.ttl_heap = MinHeap()
        
        self.maxmemory = 0  # 0은 무제한
        self.used_memory = 0
        self.evicted_keys = 0

    def _calculate_size(self, key: str, value: str) -> int:
        """주어진 key와 value의 바이트 길이를 계산"""
        return len(key.encode('utf-8')) + len(value.encode('utf-8'))

    def _check_and_expire(self, key: str) -> bool:
        """
        키가 만료되었는지 실시간으로 확인하고, 만료되었으면 삭제 처리 (Lazy Deletion)
        만료되어 삭제되었다면 True, 아니면 False 반환
        """
        entry = self.db.get(key)
        if not entry:
            return False
        
        if entry.expire_at is not None and time.time() >= entry.expire_at:
            # 완전히 만료됨 -> 전체 데이터 구조에서 제거
            self._free_key_resources(key, entry)
            return True
        return False

    def _free_key_resources(self, key: str, entry: HashEntry):
        """특정 키의 데이터를 해시맵, LRU 리스트에서 제거하고 메모리를 차감함"""
        # 메모리 차감
        entry_size = self._calculate_size(key, entry.value)
        self.used_memory -= entry_size
        
        # LRU 리스트에서 제거
        self.lru_list.remove_node(entry.lru_node)
        
        # 해시맵에서 제거
        self.db.remove(key)

    def _evict_lru(self):
        """maxmemory 초과 시 LRU 노드를 제거 규칙에 따라 축출"""
        while self.maxmemory > 0 and self.used_memory > self.maxmemory:
            lru_node = self.lru_list.remove_back()
            if not lru_node:
                # 제거할 수 있는 노드가 없음에도 초과한 특수 케이스 예방
                break
            
            key = lru_node.key
            entry = lru_node.value  # Node의 value가 HashEntry임
            
            # 해시맵에서 제거 및 메모리 반환
            entry_size = self._calculate_size(key, entry.value)
            self.used_memory -= entry_size
            self.db.remove(key)
            
            self.evicted_keys += 1

    # ------------------ 명령어 처리 함수들 ------------------

    def set_cmd(self, key: str, value: str) -> str:
        # 1. 만료 여부 먼저 검사 및 정리
        self._check_and_expire(key)
        
        new_size = self._calculate_size(key, value)
        
        # 단일 엔트리가 maxmemory를 단독으로 초과하는지 체크
        if self.maxmemory > 0 and new_size > self.maxmemory:
            return "(error) OOM command not allowed when used_memory > 'maxmemory'"

        existing_entry = self.db.get(key)
        if existing_entry:
            # 기존 키 존재 시: 메모리 갱신 및 기존 TTL 파괴
            old_size = self._calculate_size(key, existing_entry.value)
            self.used_memory = self.used_memory - old_size + new_size
            
            existing_entry.value = value
            existing_entry.expire_at = None  # TTL 초기화
            self.lru_list.move_to_front(existing_entry.lru_node)
        else:
            # 새 키 추가 시
            self.used_memory += new_size
            lru_node = Node(key, None)
            self.lru_list.insert_front(lru_node)
            
            entry = self.db.put(key, value, lru_node)
            lru_node.value = entry  # 상호 참조 연동

        # LRU Eviction 발동 검사
        self._evict_lru()
        return "OK"

    def get_cmd(self, key: str) -> str:
        if self._check_and_expire(key):
            return "(nil)"
            
        entry = self.db.get(key)
        if not entry:
            return "(nil)"
            
        # 성공 시에만 LRU 갱신
        self.lru_list.move_to_front(entry.lru_node)
        return f'"{entry.value}"'

    def del_cmd(self, key: str) -> str:
        if self._check_and_expire(key):
            return "(integer) 0"
            
        entry = self.db.get(key)
        if not entry:
            return "(integer) 0"
            
        self._free_key_resources(key, entry)
        return "(integer) 1"

    def exists_cmd(self, key: str) -> str:
        if self._check_and_expire(key):
            return "(integer) 0"
            
        if self.db.contains(key):
            return "(integer) 1"
        return "(integer) 0"

    def dbsize_cmd(self) -> str:
        # 정확한 정리를 위해 만료 힙의 일부분 청소 또는 전체 키 체크
        # 여기서는 전체 키를 순회하며 만료된 것들을 사전에 드롭시킵니다.
        all_keys = self.db.keys()
        for k in all_keys:
            self._check_and_expire(k)
        return f"(integer) {self.db.size()}"

    def keys_cmd(self) -> str:
        all_keys = self.db.keys()
        # 출력 전 일괄 만료 점검
        valid_keys = []
        for k in all_keys:
            if not self._check_and_expire(k):
                valid_keys.append(k)
                
        if len(valid_keys) == 0:
            return "(empty array)"
            
        # 개별 키 출력 포맷 구성
        return "\n".join([f'{i+1}) "{k}"' for i, k in enumerate(valid_keys)])

    def config_set_maxmemory(self, bytes_str: str) -> str:
        try:
            val = int(bytes_str)
            if val < 0:
                return "(error) ERR value is not an integer or out of range"
            self.maxmemory = val
            # 바뀐 제한량에 맞춰 초과 시 바로 탈락 실행
            self._evict_lru()
            return "OK"
        except ValueError:
            return "(error) ERR value is not an integer or out of range"

    def info_memory_cmd(self) -> str:
        lines = [
            f"used_memory:{self.used_memory}",
            f"maxmemory:{self.maxmemory}",
            f"evicted_keys:{self.evicted_keys}"
        ]
        return "\n".join(lines)

    def expire_cmd(self, key: str, seconds_str: str) -> str:
        if self._check_and_expire(key):
            return "(integer) 0"
            
        entry = self.db.get(key)
        if not entry:
            return "(integer) 0"
            
        try:
            seconds = int(seconds_str)
        except ValueError:
            return "(error) ERR value is not an integer or out of range"
            
        if seconds <= 0:
            # 즉시 만료 처리 요구사항 충족
            self._free_key_resources(key, entry)
            return "(integer) 1"
            
        expire_at = time.time() + seconds
        entry.expire_at = expire_at
        self.ttl_heap.push((expire_at, key))
        return "(integer) 1"

    def ttl_cmd(self, key: str) -> str:
        if self._check_and_expire(key):
            return "(integer) -2"
            
        entry = self.db.get(key)
        if not entry:
            return "(integer) -2"
            
        if entry.expire_at is None:
            return "(integer) -1"
            
        remaining = int(round(entry.expire_at - time.time()))
        # 반올림 등으로 인해 간헐적으로 음수가 나오면 만료 직전이므로 0 이하 처리
        return f"(integer) {max(0, remaining)}"


def parse_arguments(cmd_line: str) -> list:
    """공백 기준 분할하되, 큰따옴표 내부는 공백을 보존하는 파서 구현"""
    args = []
    current = []
    in_quotes = False
    i = 0
    while i < len(cmd_line):
        char = cmd_line[i]
        if char == '"':
            in_quotes = not in_quotes
        elif char == ' ' and not in_quotes:
            if current:
                args.append("".join(current))
                current = []
        else:
            current.append(char)
        i += 1
    if current:
        args.append("".join(current))
    return args


def main():
    redis = MiniRedis()
    
    while True:
        try:
            # 프롬프트 출력
            sys.stdout.write("mini-redis> ")
            sys.stdout.flush()
            
            line = sys.stdin.readline()
            if not line:  # EOF 처리 (Ctrl+D 등)
                break
                
            line = line.strip()
            if not line:
                continue
                
            args = parse_arguments(line)
            if not args:
                continue
                
            cmd = args[0].upper()
            
            # 종료 명령어
            if cmd in ("EXIT", "QUIT"):
                break
                
            # 명령어 라우팅 & 인자 개수 밸리데이션
            if cmd == "SET":
                if len(args) != 3:
                    print("(error) ERR wrong number of arguments for 'set' command")
                else:
                    print(redis.set_cmd(args[1], args[2]))
                    
            elif cmd == "GET":
                if len(args) != 2:
                    print("(error) ERR wrong number of arguments for 'get' command")
                else:
                    print(redis.get_cmd(args[1]))
                    
            elif cmd == "DEL":
                if len(args) != 2:
                    print("(error) ERR wrong number of arguments for 'del' command")
                else:
                    print(redis.del_cmd(args[1]))
                    
            elif cmd == "EXISTS":
                if len(args) != 2:
                    print("(error) ERR wrong number of arguments for 'exists' command")
                else:
                    print(redis.exists_cmd(args[1]))
                    
            elif cmd == "DBSIZE":
                if len(args) != 1:
                    print("(error) ERR wrong number of arguments for 'dbsize' command")
                else:
                    print(redis.dbsize_cmd())
                    
            elif cmd == "KEYS":
                if len(args) != 1:
                    print("(error) ERR wrong number of arguments for 'keys' command")
                else:
                    print(redis.keys_cmd())
                    
            elif cmd == "CONFIG":
                if len(args) != 4 or args[1].upper() != "SET" or args[2].lower() != "maxmemory":
                    print("(error) ERR unknown command or wrong number of arguments for 'config'")
                else:
                    print(redis.config_set_maxmemory(args[3]))
                    
            elif cmd == "INFO":
                if len(args) != 2 or args[1].lower() != "memory":
                    print("(error) ERR unknown command or wrong number of arguments for 'info'")
                else:
                    print(redis.info_memory_cmd())
                    
            elif cmd == "EXPIRE":
                if len(args) != 3:
                    print("(error) ERR wrong number of arguments for 'expire' command")
                else:
                    print(redis.expire_cmd(args[1], args[2]))
                    
            elif cmd == "TTL":
                if len(args) != 2:
                    print("(error) ERR wrong number of arguments for 'ttl' command")
                else:
                    print(redis.ttl_cmd(args[1]))
                    
            else:
                print(f"(error) ERR unknown command '{args[0]}'")
                
        except KeyboardInterrupt:
            print("\nUse 'exit' or 'quit' to end the program.")
        except Exception as e:
            print(f"(error) ERR unexpected internal error: {e}")


if __name__ == "__main__":
    main()