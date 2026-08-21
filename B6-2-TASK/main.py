import os
import sys
import re
import subprocess
import argparse
from google import genai
from google.genai import types


def get_git_changes():
    """Git 변경 사항(status, diff)을 수집하고 변경 유무를 검증하는 함수"""
    try:
        # 1. 파일 상태 수집
        status_res = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True
        )
        status_text = status_res.stdout.strip()

        # 변경 사항이 없을 경우 즉시 정상 종료
        if not status_text:
            print("\n[알림] 변경 사항이 없습니다. 작업 트리가 깨끗합니다.")
            sys.exit(0)

        # 2. Staged 변경 사항 수집 (git diff --cached)
        diff_res = subprocess.run(
            ["git", "diff", "--cached"],
            capture_output=True,
            text=True,
            check=True
        )
        diff_text = diff_res.stdout.strip()

        # Staged diff가 없으면 Unstaged diff 수집
        if not diff_text:
            diff_res = subprocess.run(
                ["git", "diff"],
                capture_output=True,
                text=True,
                check=True
            )
            diff_text = diff_res.stdout.strip()

        return status_text, diff_text

    except FileNotFoundError:
        print("[오류] Git이 설치되어 있지 않거나 환경변수 PATH에 등록되지 않았습니다.")
        sys.exit(1)
    except subprocess.CalledProcessError:
        print("[오류] 현재 디렉토리가 Git 저장소가 아닙니다. 'git init' 후 실행하세요.")
        sys.exit(1)


def apply_safe_mode(diff_text, safe_mode=True):
    """민감정보 마스킹 및 diff 길이를 제한하여 보안을 보호하는 함수"""
    if not safe_mode:
        return diff_text

    # (A) 정규식을 이용한 토큰/키/이메일 패턴 마스킹
    masked_diff = re.sub(
        r'(?i)(api[_-]?key|secret|token|password)[\s:=]+([\'"][^\'"\s]+[\'"]|[^\s]+)',
        r'\1: [MASKED]',
        diff_text
    )
    masked_diff = re.sub(
        r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+',
        '[EMAIL_MASKED]',
        masked_diff
    )

    # (B) diff 라인 수 제한 (최대 200줄 초과 시 생략)
    lines = masked_diff.splitlines()
    if len(lines) > 200:
        masked_diff = "\n".join(lines[:200]) + "\n\n... [Safe Mode: diff가 200줄을 초과하여 축약되었습니다]"

    return masked_diff


def generate_ai_draft(command_type, status_text, diff_text, model, temperature, max_tokens):
    """Gemini API를 단 1회 호출하여 초안을 생성하는 함수"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[오류] AI API Key가 설정되지 않았습니다. 'GEMINI_API_KEY' 환경변수를 설정해주세요.")
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    if command_type == "commit":
        system_instruction = (
            "당신은 숙련된 소프트웨어 엔지니어입니다. 제공된 Git 변경사항을 기반으로 최적의 커밋 메시지를 작성하세요.\n"
            "규칙:\n"
            "1. 첫 번째 줄에는 50자 이내(최대 72자)의 명확하고 간결한 커밋 제목을 작성하세요.\n"
            "2. 한 줄을 띄운 뒤, 본문에는 변경된 파일/모듈을 명시하고 핵심 변경 내용을 1~2개의 불릿(-) 포인트로 요약하세요."
        )
    else:  # pr
        system_instruction = (
            "당신은 숙련된 소프트웨어 엔지니어입니다. 제공된 Git 변경사항을 기반으로 Pull Request 초안을 작성하세요.\n"
            "규칙:\n"
            "1. 첫 줄은 80자 이내의 PR 제목을 작성하세요.\n"
            "2. 본문은 반드시 다음 3개의 마크다운 헤더를 포함해야 하며, 각 섹션 아래에 최소 1개 이상의 불릿(-) 목록을 작성하세요.\n"
            "### Why\n"
            "### What\n"
            "### How to Test"
        )

    user_content = f"### Git Status\n{status_text}\n\n### Git Diff\n{diff_text}"

    try:
        # 단 1회 호출로 제약사항 준수
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=temperature,
            max_output_tokens=max_tokens
        )
        
        response = client.models.generate_content(
            model=model,
            contents=user_content,
            config=config
        )
        
        print("\n[AI API 로그] Gemini API 1회 호출 완료.")
        return response.text.strip()

    except Exception as e:
        print(f"[오류] AI API 호출 실패: {str(e)}")
        sys.exit(1)


def display_output(command_type, result_text):
    """결과물을 터미널 구획선으로 분리하고 길이 제약 등을 검증/출력하는 함수"""
    lines = result_text.splitlines()
    first_line = lines[0] if lines else ""

    print("\n" + "=" * 65)
    print(f"       AI 생성 결과: {command_type.upper()} 초안 (검토 후 복사하여 사용)")
    print("=" * 65)

    # 길이 검증 피드백
    if command_type == "commit" and len(first_line) > 72:
        print(f"[알림] 커밋 제목이 72자를 초과했습니다 ({len(first_line)}자). 검토 후 조정하세요.\n")
    elif command_type == "pr" and len(first_line) > 80:
        print(f"[알림] PR 제목이 80자를 초과했습니다 ({len(first_line)}자). 검토 후 조정하세요.\n")

    print(result_text)
    print("=" * 65 + "\n")


def main():
    """CLI 옵션 정의 및 전체 파이프라인 제어"""
    parser = argparse.ArgumentParser(description="Git 변경사항 기반 커밋/PR 자동 생성 CLI 도구")
    parser.add_argument("command", choices=["commit", "pr"], help="생성할 작업 선택 (commit 또는 pr)")
    parser.add_argument("--model", default="gemini-3.6-flash", help="사용할 Gemini 모델 (기본값: gemini-3.6-flash)")
    parser.add_argument("--temperature", type=float, default=0.2, help="생성 온도 (기본값: 0.2)")
    parser.add_argument("--max-tokens", type=int, default=500, help="최대 생성 토큰 수 (기본값: 500)")
    parser.add_argument("--no-safe-mode", dest="safe_mode", action="store_false", default=True, help="안전 모드 비활성화")

    args = parser.parse_args()

    # 1. Git 변경 사항 수집
    status_text, diff_text = get_git_changes()

    # 2. 민감정보 마스킹 및 diff 축약
    processed_diff = apply_safe_mode(diff_text, safe_mode=args.safe_mode)

    # 3. Gemini API 단일 호출
    draft_result = generate_ai_draft(
        command_type=args.command,
        status_text=status_text,
        diff_text=processed_diff,
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens
    )

    # 4. 검증 및 결과 구획 출력
    display_output(args.command, draft_result)


if __name__ == "__main__":
    main()