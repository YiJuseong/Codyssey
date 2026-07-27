import time
from models import Commit
from algorithms import merge_sort, get_topological_sort, find_shortest_path, get_ancestors

class GitCommandHandler:
    """CLI 명령을 받아 MiniGitRepository와 알고리즘을 연결하는 처리기"""
    def __init__(self, repo):
        self.repo = repo

    def init(self, user_name):
        self.repo.current_user = user_name
        self.repo.commits = {}
        self.repo.branches = {"main": None}
        self.repo.head_branch = "main"
        self.repo.commit_counter = 1
        self.repo.index_keyword = {}
        self.repo.index_author = {}
        return f"Initialized empty Mini Git repository for user '{user_name}'"

    def branch(self, branch_name):
        if not self.repo.is_initialized():
            return "Repository not initialized. Run INIT first."
        if branch_name in self.repo.branches:
            return f"Branch '{branch_name}' already exists."
        
        current_commit = self.repo.branches[self.repo.head_branch]
        self.repo.branches[branch_name] = current_commit
        return f"Branch '{branch_name}' created."

    def switch(self, branch_name):
        if not self.repo.is_initialized():
            return "Repository not initialized. Run INIT first."
        if branch_name not in self.repo.branches:
            return f"Unknown branch: {branch_name}"
        
        self.repo.head_branch = branch_name
        return f"Switched to branch '{branch_name}'"

    def commit(self, message):
        if not self.repo.is_initialized():
            return "Repository not initialized. Run INIT first."
        
        parent_hash = self.repo.branches[self.repo.head_branch]
        parents = [parent_hash] if parent_hash else []
        
        commit_hash = self.repo.generate_hash()
        timestamp = time.time()
        
        new_commit = Commit(commit_hash, message, self.repo.current_user, timestamp, parents)
        
        self.repo.commits[commit_hash] = new_commit
        self.repo.update_index(new_commit)
        self.repo.branches[self.repo.head_branch] = commit_hash
        
        return f"[{commit_hash}] Committed successfully: \"{message}\""

    def log(self, sort_option=None):
        if not self.repo.is_initialized():
            return "Repository not initialized. Run INIT first.", False
            
        current_head = self.repo.branches.get(self.repo.head_branch)
        if not current_head:
            return "No commits found in the current branch.", False

        # 1. 옵션 검증
        if sort_option not in (None, "date", "author"):
            return "Invalid args (Valid sort types: date, author)", False

        # 2. 옵션별 분기 처리 (불필요한 위상 정렬 연산 방지)
        if sort_option is None:
            # 정렬 옵션이 없으면 부모-자식 위상 정렬
            result = get_topological_sort(self.repo.commits)
        elif sort_option == "date":
            # 전체 커밋 대상 날짜순 정렬
            commits_list = list(self.repo.commits.values())
            result = merge_sort(commits_list, lambda a, b: a.timestamp < b.timestamp)
        elif sort_option == "author":
            # 전체 커밋 대상 작성자순 정렬
            commits_list = list(self.repo.commits.values())
            result = merge_sort(commits_list, lambda a, b: a.author < b.author)

        return result, True

    def path(self, c1, c2):
        if c1 not in self.repo.commits or c2 not in self.repo.commits:
            errors = []
            if c1 not in self.repo.commits: errors.append(f"Unknown commit: {c1}")
            if c2 not in self.repo.commits and c1 != c2: errors.append(f"Unknown commit: {c2}")
            return "\n".join(errors), False
            
        path_list = find_shortest_path(self.repo.commits, c1, c2)
        if path_list:
            return "->".join(path_list), True
        else:
            return "No path", True

    def ancestors(self, target_hash):
        if target_hash not in self.repo.commits:
            return f"Unknown commit: {target_hash}", False
            
        return get_ancestors(self.repo.commits, target_hash), True

    def search(self, arg):
        result_hashes = set()
        if arg.startswith("--author="):
            author_query = arg.split("=")[1].lower()
            result_hashes = self.repo.index_author.get(author_query, set())
        else:
            kw_query = arg.lower()
            result_hashes = self.repo.index_keyword.get(kw_query, set())
            
        if not result_hashes:
            return "No matching commits found.", False
            
        matched_commits = [self.repo.commits[h] for h in result_hashes]
        sorted_matches = merge_sort(matched_commits, lambda a, b: a.hash < b.hash)
        return sorted_matches, True
    
    def get_current_branch(self):
        """현재 활성화된 브랜치명을 동적으로 반환 (초기화 전이면 NO-REPO 반환)"""
        if not self.repo.is_initialized or not self.repo.head_branch:
            return "NO-REPO"
        return self.repo.head_branch