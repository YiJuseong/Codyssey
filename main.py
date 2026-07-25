import re
from models import MiniGitRepository
from commands import GitCommandHandler

def parse_arguments(cmd_str):
    """공백 규칙 및 따옴표 기법을 처리하여 토큰 리스트로 파싱"""
    # 따옴표 내부 묶음 문자열과 일반 공백 단어를 분리하여 매칭
    tokens = re.findall(r'(?:[^\s"]+|"[^"]*")', cmd_str)
    return [t.strip('"') for t in tokens]


def main():
    repo = MiniGitRepository()
    handler = GitCommandHandler(repo)
    
    print("=== Welcome to Mini Git CLI ===")
    print("Type 'EXIT' or 'QUIT' to close the program.\n")
    
    while True:
        try:
            current_branch = handler.get_current_branch()
            raw_input = input(f"[{current_branch}] > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye.")
            break
            
        if not raw_input:
            continue
            
        tokens = parse_arguments(raw_input)
        if not tokens:
            continue
            
        cmd = tokens[0].upper()
        
        # 종료 처리
        if cmd in ("EXIT", "QUIT"):
            print("Terminating Mini Git session. Goodbye.")
            break
            
        # 1. INIT
        if cmd == "INIT":
            if len(tokens) < 2:
                print("Invalid args (Usage: INIT <user_name>)")
                continue
            user_name = " ".join(tokens[1:])
            print(handler.init(user_name))
            
        # 2. BRANCH
        elif cmd == "BRANCH":
            if len(tokens) != 2:
                print("Invalid args (Usage: BRANCH <branch_name>)")
                continue
            print(handler.branch(tokens[1]))
            
        # 3. SWITCH
        elif cmd == "SWITCH":
            if len(tokens) != 2:
                print("Invalid args (Usage: SWITCH <branch_name>)")
                continue
            print(handler.switch(tokens[1]))
            
        # 4. COMMIT
        elif cmd == "COMMIT":
            if len(tokens) < 2:
                print("Invalid args (Usage: COMMIT <message>)")
                continue
            print(handler.commit(tokens[1]))
            
        # 5. LOG
        elif cmd == "LOG":
            sort_option = None
            if len(tokens) == 2 and tokens[1].startswith("--sort-by="):
                sort_option = tokens[1].split("=")[1].lower()
            elif len(tokens) > 1:
                print("Invalid args (Usage: LOG or LOG --sort-by=date|author)")
                continue
                
            res, success = handler.log(sort_option)
            if success:
                for commit in res:
                    print(commit)
            else:
                print(res)  # 에러 메시지 출력
                
        # 6. PATH
        elif cmd == "PATH":
            if len(tokens) != 3:
                print("Invalid args (Usage: PATH <commit1> <commit2>)")
                continue
            res, _ = handler.path(tokens[1], tokens[2])
            print(res)
                
        # 7. ANCESTORS
        elif cmd == "ANCESTORS":
            if len(tokens) != 2:
                print("Invalid args (Usage: ANCESTORS <commit_hash>)")
                continue
            res, success = handler.ancestors(tokens[1])
            if success:
                for c in res:
                    print(c)
            else:
                print(res)
                    
        # 8. SEARCH
        elif cmd == "SEARCH":
            if len(tokens) != 2:
                print("Invalid args (Usage: SEARCH <keyword> or SEARCH --author=<name>)")
                continue
            res, success = handler.search(tokens[1])
            if success:
                for c in res:
                    print(c)
            else:
                print(res)
        else:
            print("Unknown command. Please check your syntax.")


if __name__ == "__main__":
    main()