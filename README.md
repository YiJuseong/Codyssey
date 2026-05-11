# 1. 기본 보안 및 네트워크 설정
## 1. SSH 접속포트 20022로 변경, Root 원격 로그인 차단 설정 및 확인
![alt text](./image/image.png)
![alt text](./image/image-1.png)
![alt text](./image/image-2.png)
## 2. 소켓 파일 수정 및 포트 변경이 적용됨을 확인
![alt text](./image/image-3.png)
![alt text](./image/image-4.png)
![alt text](./image/image-5.png)
![alt text](./image/image-6.png)
## 3. 기본 정책 설정 (모든 인바운드 차단, 아웃바운드 허용)
![alt text](./image/image-7.png)
## 4. 인바운드 허용 포트는 TCP 20022(SSH), TCP 15034(APP)만 허용
![alt text](./image/image-8.png)
## 5. UFW 방화벽 설정이 적용됨을 확인
![alt text](./image/image-9.png)

# 2. 계정/그룹/권한 체계(협업 + 최소 권한)
## 1. 그룹 생성
![alt text](./image/image-10.png)
## 2. 계정 생성 및 그룹에 추가
![alt text](./image/image-11.png)
## 3. 디렉토리 생성
![alt text](./image/image-12.png)
## 4. 소유권 설정
![alt text](./image/image-13.png)
## 5. 권한 및 SetGID 설정
![alt text](./image/image-14.png)
## 6. 계정 그룹 확인
![alt text](./image/mage-15.png)
## 7. ls -l 로 소유/권한 확인
![alt text](./image/image-16.png)
## 8. getfacl로 소유/권한 확인
![alt text](./image/image-17.png)
# 3. 애플리케이션 실행 환경 구성(제공 Python 앱)
## 1. 일반 계정으로 이동
![alt text](./image/image-18.png)
## 2. 키 파일 생성
![alt text](./image/image-19.png)
## 3. 환경 변수 설정
![alt text](./image/image-20.png)
## 4. 앱 실행 및 종료
![alt text](./image/image-21.png)
# 4. 시스템 관제 자동화 스크립트 (monitor.sh) 구현
## 1. monitor.sh 구현 및 log 폴더 생성
![alt text](./image/image-22.png)
![alt text](./image/image-23.png)
![alt text](./image/image-24.png)
## 2. monitor.sh 실행이 되는지 확인
![alt text](./image/image-25.png)
## 3. 권한 및 파일 정책 설정
![alt text](./image/image-26.png)
## 4. cron 설정
![alt text](./image/image-27.png)
## 5. 1분마다 로그가 기록되는지 확인
![alt text](./image/image-28.png)