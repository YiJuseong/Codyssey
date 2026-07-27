import time

class Commit:
    """커밋 그래프의 노드를 나타내는 클래스 (DAG 구조)"""
    def __init__(self, commit_hash, message, author, timestamp, parents):
        self.hash = str(commit_hash)
        self.message = message
        self.author = author
        self.timestamp = timestamp  # float (Unix Epoch Time)
        self.parents = parents      # List of commit_hash strings

    def __repr__(self):
        time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.timestamp))
        return f"[{self.hash}] {self.author} | {time_str} | {self.message}"


class MiniGitRepository:
    """인메모리 커밋 저장소 및 역색인(Inverted Index) 관리 클래스"""
    def __init__(self):
        self.current_user = None
        self.commits = {}           # hash -> Commit 객체
        self.branches = {}          # branch_name -> commit_hash
        self.head_branch = None     # 현재 활성화된 브랜치 이름
        self.commit_counter = 1     # 유일한 커밋 해시 생성을 위한 카운터
        
        # 역색인 (Inverted Index) 저장소
        self.index_keyword = {}     # keyword (lower) -> set of commit_hashes
        self.index_author = {}      # author (lower) -> set of commit_hashes

    def is_initialized(self):
        return self.current_user is not None

    def generate_hash(self):
        """세션 내에서 중복되지 않는 고유한 커밋 해시 생성"""
        h = f"c{self.commit_counter}"
        self.commit_counter += 1
        return h

    def _tokenize(self, text):
        """텍스트를 소문자로 정규화하고 공백 기준으로 토큰화 (특수문자 제거)"""
        if not text:
            return []
        tokens = text.lower().split()
        return [t.strip(",.?!\"'") for t in tokens if t.strip(",.?!\"'")]

    def update_index(self, commit):
        """새로 생성된 커밋을 역색인 구조에 반영"""
        # 1. 키워드 인덱스 업데이트 (커밋 메시지 기반)
        keywords = self._tokenize(commit.message)
        for kw in keywords:
            if kw not in self.index_keyword:
                self.index_keyword[kw] = set()
            self.index_keyword[kw].add(commit.hash)
        
        # 2. 작성자 인덱스 업데이트
        author_lower = commit.author.lower()
        if author_lower not in self.index_author:
            self.index_author[author_lower] = set()
        self.index_author[author_lower].add(commit.hash)