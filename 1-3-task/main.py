from cProfile import label
import json
import time

class MACAnalyzer:
    def __init__(self):
        self.filters = {}  # {size: {'Cross': [[...]], 'X': [[...]]}}
        self.epsilon = 1e-9

    # --- 유틸리티 및 정규화 ---
    def normalize_label(self, label):
        try:
        # 1. 입력값의 유효성 검사 (None이거나 비어있는 경우)
            if label is None:
                return "Unknown"

        # 2. 문자열로 변환 후 전처리 (소문자화, 양끝 공백 제거)
            clean_label = str(label).lower().strip()

        # 3. 빈 문자열인 경우 예외 처리
            if not clean_label:
                return "Unknown"

        # 4. 키워드 기반 정규화 (유연한 매칭)
        # '+' 기호이거나 'cross'라는 단어가 포함되어 있으면 "Cross"
            if clean_label == '+' or 'cross' in clean_label:
                return "Cross"
        
        # 'x'라는 단어가 포함되어 있으면 "X" 
        # (주의: 'cross'에도 'x'가 포함되므로 'cross'를 먼저 검사해야 함)
            if 'x' in clean_label:
                return "X"

        # 5. 매칭되는 것이 없으면 전처리된 라벨 그대로 반환
            return clean_label

        except Exception as e:
            print(f"[Warning] Label normalization error: {e}")
            return str(label)
    def validate_input(self, size, prompt):
        print(f"{prompt} ({size}x{size})을 입력하세요:")
        matrix = []
        while len(matrix) < size:
            try:
                line = input(f"{len(matrix) + 1}행: ").split()
                if len(line) != size:
                    raise ValueError(f"열 개수 불일치: {size}개의 숫자가 필요합니다.")
                row = [float(x) for x in line]
                matrix.append(row)
            except ValueError as e:
                print(f"입력 형식 오류: {e} 다시 입력하세요.")
        return matrix

    # --- 핵심 MAC 연산 (순수 반복문) ---
    def calculate_mac(self, pattern, filter_data):
        t_start = time.perf_counter()
        
        size = len(pattern)
        score = 0.0
        for i in range(size):
            for j in range(size):
                score += pattern[i][j] * filter_data[i][j]
        
        t_end = time.perf_counter()
        elapsed_ms = (t_end - t_start) * 1000
        
        return score, elapsed_ms

    # --- 모드 1: 3x3 사용자 입력 ---
    def run_manual_mode(self):
        print("\n[모드 1: 3x3 사용자 입력]")
        filter_a = self.validate_input(3, "필터 A")
        filter_b = self.validate_input(3, "필터 B")
        pattern = self.validate_input(3, "입력 패턴")

        iteration_times = []

        for _ in range(10):
            score_a, time_a = self.calculate_mac(pattern, filter_a)
            score_b, time_b = self.calculate_mac(pattern, filter_b)
            iteration_times.append(time_a + time_b)

        avg_duration_ms = sum(iteration_times) / len(iteration_times)
        
        result = "UNDECIDED"
        if abs(score_a - score_b) < self.epsilon:
            result = "판정 불가"
        elif score_a > score_b:
            result = "A"
        else:
            result = "B"

        print("\n--- 결과 ---")
        print(f"필터 A 점수: {score_a:.4f} | 필터 B 점수: {score_b:.4f}")
        print(f"연산 시간: {avg_duration_ms:.6f} ms")
        print(f"판정 결과: {result}")
        
        self.print_performance_table([(3, avg_duration_ms)])

    # --- 모드 2: JSON 분석 ---
    def run_json_mode(self):
        print("\n[모드 2: data.json 분석]")
        try:
            with open('data.json', 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            print("오류: data.json 파일이 없습니다.")
            return

        # 필터 로드 및 정규화
        raw_filters = data.get('filters', {})
        structured_filters = {}
        for key, val in raw_filters.items():
            size = int(key.split('_')[1])
            if size not in structured_filters:
                structured_filters[size] = {}
            for f_type, f_mat in val.items():
                norm_type = self.normalize_label(f_type)
                structured_filters[size][norm_type] = f_mat

        results = []
        perf_data = {} # {size: [times]}

        patterns = data.get('patterns', {})
        for key, p_data in patterns.items():
            size_n = int(key.split('_')[1])
            input_mat = p_data.get('input')
            expected = self.normalize_label(p_data.get('expected'))
            
            # 검증: 크기 불일치
            if len(input_mat) != size_n or any(len(row) != size_n for row in input_mat):
                results.append({'id': key, 'status': 'FAIL', 'reason': f"Size mismatch (Expected {size_n})"})
                continue

            current_filters = structured_filters.get(size_n)

            if not current_filters:
                results.append({'id': key, 'status': 'FAIL', 'reason': f"No filters found for size {size_n}"})
                continue
            filter_error = False
            for lbl, f_mat in current_filters.items():
                if len(f_mat) != size_n or any(len(row) != size_n for row in f_mat):
                    results.append({'id': key, 'status': 'FAIL', 'reason': f"Filter '{lbl}' size mismatch"})
                    filter_error = True
                    break
            
            if filter_error:
                continue

            # 성능 측정 (10회 반복)
            times = []
            available_labels = list(current_filters.keys())
            
            for _ in range(10):
                t_total_loop = 0 # 이번 회차의 모든 필터 연산 합계 시간
                current_scores = {}
                
                for lbl in available_labels:
        # 수정된 함수 호출 (점수와 소요시간을 따로 받음)
                    score, calc_time = self.calculate_mac(input_mat, current_filters[lbl])
                    current_scores[lbl] = score
                    t_total_loop += calc_time # 각 필터별 순수 연산 시간만 합산
        
                times.append(t_total_loop)
            
            
            perf_data.setdefault(size_n, []).extend(times)

            sorted_scores = sorted(current_scores.items(), key=lambda x: x[1], reverse=True)
            top_label, top_score = sorted_scores[0]

            second_score = sorted_scores[1][1] if len(sorted_scores) > 1 else 0            # 판정
            
            if abs(top_score - second_score) < self.epsilon:
                decision = "UNDECIDED"
            else:
                decision = top_label

            status = "PASS" if decision == expected else "FAIL"
            
            results.append({
                'id': key, 'scores': current_scores, 'dec': decision, 
                'exp': expected, 'status': status
            })

        # 결과 출력
        labels_header = " | ".join([f"{lbl:<8}" for lbl in available_labels])
        print(f"{'ID':<15} | {labels_header} | {'Decision':<10} | {'Expected':<10} | {'Status'}")
        print("-" * (45 + len(available_labels) * 11))
        
        pass_count = 0
        fail_list = []
        for r in results:
            if r['status'] == 'PASS':
                pass_count += 1
                scores_str = " | ".join([f"{r['scores'].get(lbl, 0):<8.2f}" for lbl in available_labels])
                print(f"{r['id']:<15} | {scores_str} | {r['dec']:<10} | {r['exp']:<10} | PASS")
            else:
                fail_list.append(r)
                reason = r.get('reason', 'Wrong Decision')

                dec = r.get('dec', 'N/A')
                exp = r.get('exp', 'N/A')
                print(f"{r['id']:<15} | FAIL ({reason}) -> Dec: [{dec}] vs Exp: [{exp}]")
               
                if 'dec' in r and r['dec'] == "UNDECIDED":
                    # 1등과 2등 점수 차이를 출력해서 epsilon 범위인지 확인
                    sorted_s = sorted(r['scores'].items(), key=lambda x: x[1], reverse=True)
                    diff = sorted_s[0][1] - sorted_s[1][1]
                    print(f"      [!] Tie detected. Diff: {diff:.12f} (Epsilon: {self.epsilon})")

        print("\n[최종 리포트]")
        print(f"전체: {len(results)} / 통과: {pass_count} / 실패: {len(fail_list)}")
        if fail_list:
            print("실패 케이스 목록:")
            for f in fail_list:
                reason = f.get('reason', 'Unknown Error')
                print(f"- {f['id']}: {reason}")

                if 'dec' in f:
                    print(f"  [상세] 판정: {f['dec']} / 기대값: {f['exp']}")
                    if f['dec'] == "UNDECIDED":
            # 동점인 경우 점수 차이 출력 로직
                        sorted_s = sorted(f['scores'].items(), key=lambda x: x[1], reverse=True)
                        diff = sorted_s[0][1] - sorted_s[1][1]
                        print(f"  [!] 동점 감지 (차이: {diff:.12f})")

        # 성능 분석 표
        avg_perfs = [(sz, sum(t_list)/len(t_list)) for sz, t_list in perf_data.items()]
        self.print_performance_table(avg_perfs)

    def print_performance_table(self, perf_list):
        print("\n[성능 분석 표]")
        print(f"{'크기(NxN)':<12} | {'평균 시간(ms)':<15} | {'연산 횟수(N²)'}")
        print("-" * 50)
        for sz, avg_t in sorted(perf_list):
            print(f"{sz:<2}x{sz:<9} | {avg_t:<15.6f} | {sz*sz}")

    def main(self):
        print("=== MAC 연산 분석기 ===")
        while True: # 무한 루프 시작
            choice = input("\n모드 선택 (1: 사용자 입력, 2: JSON 분석): ").strip()
            
            if choice == '1':
                self.run_manual_mode()
                break  # 올바른 입력을 처리했으므로 루프 탈출
            elif choice == '2':
                self.run_json_mode()
                break  # 올바른 입력을 처리했으므로 루프 탈출
            else:
                # 잘못된 입력 시 안내 문구를 출력하고 다시 루프의 처음으로 돌아감
                print("잘못된 선택입니다. '1' 또는 '2'를 입력해주세요.")
        

if __name__ == "__main__":
    MACAnalyzer().main()