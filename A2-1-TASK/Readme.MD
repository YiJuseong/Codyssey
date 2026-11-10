# 수학 기초 구현: 선형대수 · 미적분 · 최적화 · 확률 · 역전파

딥러닝에 쓰이는 수학 기초를 **NumPy로 직접 구현**하고, 그림과 수치 검증으로 확인하는 프로젝트입니다.

- 계산은 NumPy만 사용합니다. Matplotlib과 Seaborn은 시각화에만 씁니다.
- `np.linalg.eig`는 Power Iteration 결과를 비교하는 검증 코드(`reference_dominant_eigenvalue`)에서만 호출합니다.
- PyTorch, TensorFlow, JAX 같은 자동미분 라이브러리와 scikit-learn은 쓰지 않습니다.
- 재현성을 위해 시드는 42로 고정합니다.

## 구조

```
.
├── src/
│   ├── linear_algebra.py   # 회전·스케일링·전단 시각화, Power Iteration, SVD 압축
│   ├── calculus.py         # 중심차분, 기울기 시각화, softmax
│   ├── optimizer.py        # VanillaGD, Momentum, 경로 시각화
│   ├── probability.py      # 정규분포 PDF, 베르누이 PMF
│   └── plot_style.py       # 공통 Matplotlib 설정(한글 폰트)
├── notebooks/
│   ├── backprop_derivation.ipynb   # 2층 신경망 순전파/역전파 유도와 손계산
│   └── probability_loss.ipynb      # MSE-MLE, Cross-Entropy-MLE 유도
├── scripts/
│   ├── run_experiments.py  # 전 요구사항 검증 + outputs/ PNG 생성
│   └── build_notebooks.py  # 노트북 JSON 생성(노트북의 원본)
├── outputs/                # 그림(PNG)과 metrics.json
├── data/                   # SVD 실험용 64×64 회색조 이미지
└── requirements.txt
```

## 실행 방법

Python 3.8 이상이 필요합니다. 프로젝트 루트에서 실행합니다.

```bash
pip install -r requirements.txt
python scripts/run_experiments.py      # 검증 + outputs/*.png + outputs/metrics.json
jupyter notebook notebooks/            # 노트북 열기
```

노트북을 처음부터 다시 만들려면 `python scripts/build_notebooks.py`를 실행합니다. 이 스크립트는 실행 결과가 없는 노트북을 쓰므로, 결과를 남기려면 다음으로 실행해서 저장합니다.

```bash
jupyter nbconvert --to notebook --execute --inplace notebooks/*.ipynb
```

`run_experiments.py`는 조건을 만족하지 못하면 `AssertionError`로 멈춥니다.

## 주요 결과

| 항목 | 기준 | 결과 |
| --- | --- | --- |
| 면적비 vs \|det(A)\| 상대오차 (회전·스케일링·전단) | ≤ 1% | 최대 5.6e-16 |
| Power Iteration vs `np.linalg.eig` (5×5 대칭행렬) | ≤ 5% | 상대오차 6.3e-16 (λ ≈ -2.8105) |
| 중심차분 f(x)=x² at x=3 | 오차 ≤ 1e-4 | 오차 8.4e-10 (6.0000000008) |
| 기울기 화살표와 등고선 접선의 내적 | 수직 | 최댓값 0 |
| Vanilla GD, lr=0.1, 100회, f=x²+y² | 반경 ≤ 0.1 | 반경 1.2e-9 |
| Momentum, β=0.9, 같은 조건 | 비교 | 반경 1.6e-2 |
| 타원 x²+10y², 80회: Vanilla GD | 비교 | 반경 1.5 |
| 타원 x²+10y², 80회: Momentum | 반경 ≤ 0.1, Vanilla보다 작음 | 반경 3.3e-2 |
| softmax 합 오차 | ≤ 1e-6 | 2.2e-16 |
| 역전파 NumPy vs 손계산 | 소수점 4자리 일치 | 전부 일치 |
| SVD 상대 Frobenius 오차 | - | k=10: 0.109, k=50: 8.5e-5, k=100(r=64): 5.7e-15 |

### 역전파 고정 예제 (y_true = 1)

과제 문장에 정답 라벨 값이 비어 있어 1로 고정했습니다.

| 텐서 | shape | 값 |
| --- | --- | --- |
| z1 | (2,) | [0.1000, 0.3000] |
| a1 | (2,) | [0.5250, 0.5744] |
| z2 | () | 0.6072 |
| ŷ | () | 0.6473 |
| ∂L/∂ŷ | () | -1.5449 |
| ∂L/∂z2 | () | -0.3527 (= ŷ - y) |
| ∂L/∂W2 | (2,) | [-0.1852, -0.2026] |
| ∂L/∂a1 | (2,) | [-0.1764, -0.2116] |
| ∂L/∂z1 | (2,) | [-0.0440, -0.0517] |
| ∂L/∂W1 | (2, 2) | [[-0.0440, 0], [-0.0517, 0]] |

## 참고 사항

- **학습률과 발산**: f=x²+y²에서 갱신은 θ ← (1-2η)θ 입니다. η=0.5는 한 스텝에 원점에 도달하고, η=1.0은 같은 거리를 왕복하며, η>1에서 발산합니다. 그래서 `gd_divergence_bowl.png`는 0.1, 0.5, 1.0, 1.2를 함께 그립니다. (η=1.2의 12회 후 반경 약 320)
- **N(2, 0.5)의 0.5는 분산**입니다. 표준편차는 √0.5 입니다.
- 전단 행렬과 회전 행렬의 det는 1이고, S(2, 0.5)도 2×0.5=1이라 세 변환 모두 면적이 보존됩니다.

## 생성되는 그림 (`outputs/`)

`rotation_unit_circle.png`, `scaling_unit_circle.png`, `shear_unit_circle.png`, `svd_compression.png`, `gradient_contour.png`, `gd_convergence_bowl.png`, `gd_vs_momentum_bowl.png`, `gd_divergence_bowl.png`, `gd_vs_momentum_ellipse.png`, `normal_pdf.png`, `bernoulli_pmf.png`