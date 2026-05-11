import os
import sys
import socket
import time

def print_step(step, message):
    # 이미지 예시와 동일한 포맷으로 출력
    print(f"[{step}/5] {message:<30} [OK]")

def run_boot_sequence():
    print("> Starting Agent Boot Sequence...")
    time.sleep(0.3)

    # [1/5] Checking User Account
    uid = os.getuid()
    user_name = os.popen("whoami").read().strip()
    if uid == 0:
        print("Error: Root user execution is prohibited.")
        sys.exit(1)
    print_step(1, "Checking User Account")
    print(f" ... Running as service user '{user_name}' (uid={uid})")

    # [2/5] Verifying Environment Variables
    required_envs = ["AGENT_HOME", "AGENT_PORT", "AGENT_UPLOAD_DIR", "AGENT_KEY_PATH", "AGENT_LOG_DIR"]
    for env in required_envs:
        if env not in os.environ:
            print(f"Error: Environment variable {env} is missing.")
            sys.exit(1)
    print_step(2, "Verifying Environment Variables")
    print(" ... All required Envs correct")

    # [3/5] Checking Required Files
    key_path = os.environ.get("AGENT_KEY_PATH")
    if not os.path.exists(key_path):
        print(f"Error: Key file not found at {key_path}")
        sys.exit(1)
    
    with open(key_path, "r") as f:
        key_content = f.read().strip()
        if key_content != "agent_api_key_test":
            print("Error: Invalid key string.")
            sys.exit(1)
    print_step(3, "Checking Required Files")
    print(" ... Verified key file with correct key string.")

    # [4/5] Checking Port Availability
    port = int(os.environ.get("AGENT_PORT", 15034))
    # 포트가 사용 중인지 임시 확인
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("0.0.0.0", port))
        except socket.error:
            print(f"Error: Port {port} is already in use.")
            sys.exit(1)
    print_step(4, "Checking Port Availability")
    print(f" ... Port {port} is available.")

    # [5/5] Verifying Log Permission
    log_dir = os.environ.get("AGENT_LOG_DIR")
    if os.path.exists(log_dir) and os.access(log_dir, os.W_OK):
        print_step(5, "Verifying Log Permission")
        print(f" ... Log directory is writable: {log_dir}")
    else:
        print(f"Error: Log directory does not exist or no write permission: {log_dir}")
        sys.exit(1)

    print("-" * 55)
    print("All Boot Checks Passed!")
    print("Agent READY")
    print("-" * 55)

def start_application():
    port = int(os.environ.get("AGENT_PORT", 15034))
    # 표준 라이브러리 socket을 사용하여 0.0.0.0:15034 LISTEN 상태 유지
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("0.0.0.0", port))
        s.listen(5)
        try:
            while True:
                # 클라이언트 접속을 기다리며 대기 (LISTEN 상태 유지)
                conn, addr = s.accept()
                with conn:
                    conn.sendall(b"Agent Status: Online\n")
        except KeyboardInterrupt:
            print("\nStopping Agent...")
            sys.exit(0)

if __name__ == "__main__":
    run_boot_sequence()
    start_application()