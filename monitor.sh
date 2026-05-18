#!/bin/bash

# ---------------------------------------------------------
# 환경 설정
# ---------------------------------------------------------
APP_NAME="agent-app"
CHECK_PORT=15034
LOG_FILE="/var/log/agent-app/monitor.log"
CPU_LIMIT=20
MEM_LIMIT=10
DISK_LIMIT=80

echo "====== SYSTEM MONITOR RESULT ======"

# ---------------------------------------------------------
# 1. Health Check (실패 시 종료)
# ---------------------------------------------------------
echo "[HEALTH CHECK]"
PID=$(pgrep -f "$APP_NAME" | head -n 1)
if [ -z "$PID" ]; then
    echo "Checking process '$APP_NAME'... [FAILED]"
    exit 1
fi
echo "Checking process '$APP_NAME'... [OK] (PID: $PID)"

PORT_CHECK=$(ss -tuln | grep ":$CHECK_PORT ")
if [ -z "$PORT_CHECK" ]; then
    echo "Checking port $CHECK_PORT... [FAILED]"
    exit 1
fi
echo "Checking port $CHECK_PORT... [OK]"

# ---------------------------------------------------------
# 2. 상태 점검 (경고만 출력)
# ---------------------------------------------------------
UFW_STATUS=$(ufw status | grep "Status: active")
if [ -z "$UFW_STATUS" ]; then
    echo "[WARNING] Firewall is inactive."
fi

# ---------------------------------------------------------
# 3. 자원 수집 및 임계값 점검
# ---------------------------------------------------------
echo -e "\n[RESOURCE MONITORING - $APP_NAME (PID: $PID)]"

# 3-1. 앱의 CPU 및 MEM 사용량 수집 (ps 명령어로 PID 기준 추출)
# ps -p PID -o %cpu,%mem 구조를 활용하며, tail -1로 수치만 가져옵니다.
APP_RESOURCES=$(ps -p "$PID" -o %cpu,%mem | tail -1)
APP_CPU=$(echo "$APP_RESOURCES" | awk '{print $1}')
APP_MEM=$(echo "$APP_RESOURCES" | awk '{print $2}')

echo "App CPU Usage : $APP_CPU%"
echo "App MEM Usage : $APP_MEM%"

# 3-2. 앱의 DISK 사용량 수집 (앱이 설치된 디렉토리 또는 로그 디렉토리 크기)
# 프로세스 자체의 '실시간 디스크 사용량(I/O)' 보다는, 앱 폴더가 차지하는 용량을 측정하는 것이 일반적입니다.
# 여기서는 예시로 로그 파일($LOG_FILE)이 속한 디렉토리나 앱 디렉토리 용량을 확인합니다.
APP_DIR=$(dirname "$LOG_FILE") 
APP_DISK_USED=$(du -sm "$APP_DIR" | awk '{print $1}') # MB 단위 수치만 추출

echo "App Disk Used : ${APP_DISK_USED}MB"

# 임계값 경고 출력
CPU_WARN=$(awk -v cpu="$APP_CPU" -v limit="$CPU_LIMIT" 'BEGIN {print (cpu > limit) ? 1 : 0}')
if [ "$CPU_WARN" -eq 1 ]; then
    echo "[WARNING] App CPU threshold exceeded ($APP_CPU% > $CPU_LIMIT%)"
fi

# MEM 점검
MEM_WARN=$(awk -v mem="$APP_MEM" -v limit="$MEM_LIMIT" 'BEGIN {print (mem > limit) ? 1 : 0}')
if [ "$MEM_WARN" -eq 1 ]; then
    echo "[WARNING] App MEM threshold exceeded ($APP_MEM% > $MEM_LIMIT%)"
fi

# DISK 점검
if [ "$APP_DISK_USED" -gt "$DISK_LIMIT" ]; then
    echo "[WARNING] App DISK threshold exceeded (${APP_DISK_USED}MB > ${DISK_LIMIT}MB)"
fi

# ---------------------------------------------------------
# 4. 로그 기록
# ---------------------------------------------------------
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
LOG_LINE="[$TIMESTAMP] PID:$PID CPU:$APP_CPU% MEM:$APP_MEM% DISK_USED:$APP_DISK_USED%"

# 로그 디렉토리 권한 체크 및 기록
echo "$LOG_LINE" >> "$LOG_FILE"
echo -e "\n[INFO] Log appended: $LOG_FILE"

# ---------------------------------------------------------
# 5. 로그 로테이션 (간이 구현: 10MB 초과 시 rotate)
# ---------------------------------------------------------
MAX_SIZE=10485760 # 10MB
if [ -f "$LOG_FILE" ] && [ $(stat -c%s "$LOG_FILE") -gt $MAX_SIZE ]; then
    for i in {9..1}; do
        [ -f "$LOG_FILE.$i" ] && mv "$LOG_FILE.$i" "$LOG_FILE.$((i+1))"
    done
    mv "$LOG_FILE" "$LOG_FILE.1"
    touch "$LOG_FILE"
    chmod 664 "$LOG_FILE"
fi
