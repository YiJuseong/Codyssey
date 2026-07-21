def merge_sort(arr, compare_func):
    """Python 내장 sort/sorted를 사용하지 않고 직접 구현한 Merge Sort"""
    if len(arr) <= 1:
        return arr
    
    mid = len(arr) // 2
    left = merge_sort(arr[:mid], compare_func)
    right = merge_sort(arr[mid:], compare_func)
    
    return _merge(left, right, compare_func)

def _merge(left, right, compare_func):
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if compare_func(left[i], right[j]):
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result


def get_topological_sort(commits_dict, start_hash):
    """부모 커밋이 항상 자식 커밋보다 먼저 출력되도록 위상 정렬(Topological Sort)을 수행"""
    if not start_hash:
        return []

    adj = {}      # parent -> list of children
    in_degree = {} # commit_hash -> int
    
    # 1. HEAD(start_hash)로부터 역방향(조상)으로 도달 가능한 모든 노드 수집
    stack = [start_hash]
    visited = set([start_hash])
    all_nodes = set()
    
    while stack:
        curr = stack.pop()
        all_nodes.add(curr)
        commit = commits_dict.get(curr)
        if commit:
            for p in commit.parents:
                if p not in visited:
                    visited.add(p)
                    stack.append(p)

    # 차수 및 인접 리스트 초기화
    for n in all_nodes:
        in_degree[n] = 0
        adj[n] = []

    # 부모 -> 자식 방향으로 간선과 진입 차수(in-degree) 설정
    for n in all_nodes:
        commit = commits_dict.get(n)
        if commit:
            for p in commit.parents:
                if p in all_nodes:
                    adj[p].append(n)
                    in_degree[n] += 1

    # 진입 차수가 0인 노드(최상위 조상)들을 큐에 삽입 후 사전순 정렬
    queue = [n for n in all_nodes if in_degree[n] == 0]
    for i in range(len(queue)):
        for j in range(i + 1, len(queue)):
            if queue[i] > queue[j]:
                queue[i], queue[j] = queue[j], queue[i]

    order = []
    while queue:
        curr = queue.pop(0)
        order.append(commits_dict[curr])
        
        for neighbor in adj[curr]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
                
        # 동률일 때 일관된 순서를 유지하기 위해 정렬
        for i in range(len(queue)):
            for j in range(i + 1, len(queue)):
                if queue[i] > queue[j]:
                    queue[i], queue[j] = queue[j], queue[i]

    return order


def find_shortest_path(commits_dict, start_hash, end_hash):
    """무방향 간선 기준 최단 경로 구하기 (BFS)
    동률 최단 경로 발생 시 문자열(c1->c2) 조인 기준 사전순 최소 경로 선택.
    """
    if start_hash not in commits_dict or end_hash not in commits_dict:
        return None

    # 무방향 그래프 인접 리스트 구축
    graph = {}
    for h, c in commits_dict.items():
        if h not in graph: graph[h] = set()
        for p in c.parents:
            if p in commits_dict:
                if p not in graph: graph[p] = set()
                graph[h].add(p)
                graph[p].add(h)

    queue = [[start_hash]]
    visited = {start_hash: 0} # node -> distance
    all_paths = []
    min_len = float('inf')

    while queue:
        path = queue.pop(0)
        curr = path[-1]
        
        if len(path) > min_len:
            continue

        if curr == end_hash:
            if len(path) < min_len:
                min_len = len(path)
                all_paths = [path]
            elif len(path) == min_len:
                all_paths.append(path)
            continue

        for neighbor in graph.get(curr, []):
            if neighbor not in visited or visited[neighbor] == visited[curr] + 1:
                visited[neighbor] = visited[curr] + 1
                queue.append(path + [neighbor])

    if not all_paths:
        return None

    # 동률 경로 중 사전순 정렬 후 최솟값 선택
    path_strings = ["->".join(p) for p in all_paths]
    best_path_str = path_strings[0]
    best_idx = 0
    for idx, ps in enumerate(path_strings):
        if ps < best_path_str:
            best_path_str = ps
            best_idx = idx

    return all_paths[best_idx]


def get_ancestors(commits_dict, commit_hash):
    """특정 커밋에서 도달 가능한 모든 조상 커밋 탐색"""
    if commit_hash not in commits_dict:
        return None
    
    ancestors = set()
    queue = [commit_hash]
    
    while queue:
        curr = queue.pop(0)
        commit = commits_dict.get(curr)
        if commit:
            for p in commit.parents:
                if p not in ancestors:
                    ancestors.add(p)
                    queue.append(p)
                    
    res_list = [commits_dict[h] for h in ancestors]
    # 해시 문자열 기준으로 직접 정렬하여 반환
    return merge_sort(res_list, lambda a, b: a.hash < b.hash)