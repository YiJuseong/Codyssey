#!/bin/bash

# ---------------------------------------------------------
# 환경 설정
# ---------------------------------------------------------
APP_NAME="agent_app.py"
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
PID=$(pgrep -f "$APP_NAME")
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
echo -e "\n[RESOURCE MONITORING]"

# CPU Usage (1초간 측정 평균)
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2 + $4}')
echo "CPU Usage : $CPU_USAGE%"

# MEM Usage
MEM_USAGE=$(free | grep Mem | awk '{print $3/$2 * 100.0}' | xargs printf "%.1f")
echo "MEM Usage : $MEM_USAGE%"

# DISK Usage (Root partition)
DISK_USED=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
echo "DISK Used : $DISK_USED%"

# 임계값 경고 출력
if (( $(echo "$CPU_USAGE > $CPU_LIMIT" | bc -l) )); then
    echo "[WARNING] CPU threshold exceeded ($CPU_USAGE% > $CPU_LIMIT%)"
fi
if (( $(echo "$MEM_USAGE > $MEM_LIMIT" | bc -l) )); then
    echo "[WARNING] MEM threshold exceeded ($MEM_USAGE% > $MEM_LIMIT%)"
fi
if [ "$DISK_USED" -gt "$DISK_LIMIT" ]; then
    echo "[WARNING] DISK threshold exceeded ($DISK_USED% > $DISK_LIMIT%)"
fi

# ---------------------------------------------------------
# 4. 로그 기록
# ---------------------------------------------------------
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
LOG_LINE="[$TIMESTAMP] PID:$PID CPU:$CPU_USAGE% MEM:$MEM_USAGE% DISK_USED:$DISK_USED%"

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