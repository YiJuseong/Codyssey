# AWS 리소스 정리 체크리스트 (Cleanup Checklist)

실습 완료 및 증빙 자료 확보 후 불필요한 과금 발생을 방지하기 위해 생성된 모든 AWS 리소스를 정리하고 점검한 내역입니다.

---

## 1. 리소스 정리 상태 점검표

| 리소스 구분 | 리소스 이름 | 조치 내용 | 최종 상태 | 비고 |
| :--- | :--- | :--- | :---: | :--- |
| **EC2 인스턴스** |  (`task-web-server`) | 인스턴스 종료(Terminate) | **종료됨 (Terminated)** | 과금 중단 완료 |
| **EBS 볼륨** |  (8 GiB) | 루트 볼륨 자동 삭제 확인 | **삭제됨 (Deleted)** | '인스턴스 종료 시 삭제' 옵션 적용 |
| **탄력적 IP (EIP)** | - | 사용하지 않음 (퍼블릭 IP 자동할당 사용) | **해당 없음** | 잔여 EIP 없음 |
| **보안 그룹** |  (`web-sg`) | 보안 그룹 삭제 | **삭제됨 (Deleted)** | 기본 보안 그룹만 유지 |
| **서브넷** |  (`task-public-subnet-2a`) | 서브넷 삭제 | **삭제됨 (Deleted)** | - |
| **라우팅 테이블** |  (`task-public-rt`) | 라우팅 테이블 삭제 | **삭제됨 (Deleted)** | 기본 라우팅 테이블 외 삭제 |
| **인터넷 게이트웨이** | (`task-igw`) | VPC 분리(Detach) 후 삭제 | **삭제됨 (Deleted)** | - |
| **VPC** | (`task-vpc`) | VPC 삭제 | **삭제됨 (Deleted)** | 기본 VPC만 유지 |
| **IAM 사용자** | `cloud-task-user` | 과금 발생 없음 확인 | **유지 / 비활성화** | 과금 비대상 리소스 |

---

## 2. 과금 방지 최종 확인

- [x] 서울 리전(`ap-northeast-2`) 내 실행 중인(Running) EC2 인스턴스 0대 확인
- [x] 미사용 상태로 남아있는 독립 EBS(Elastic Block Store) 볼륨 0개 확인
- [x] 할당된 미사용 탄력적 IP(Elastic IP) 0개 확인
- [x] AWS Cost Management / Billing 콘솔에서 실시간 잔여 유료 리소스 없음 확인

![2](../images/billing.png)