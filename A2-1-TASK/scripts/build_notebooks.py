"""노트북 JSON을 만든다. 실행 결과는 포함하지 않는다."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]



def markdown(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": text.splitlines(keepends=True)}


def code(text: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": text.splitlines(keepends=True),
    }


def notebook(cells: list[dict]) -> dict:
    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
        "cells": cells,
    }


BACKPROP = notebook(
    [
        markdown(
            """# 2층 신경망의 순전파와 역전파

입력 2개, 은닉 2개, 출력 1개인 신경망의 순전파를 적고, 출력층에서 입력층 방향으로 연쇄 법칙을 적용해 기울기를 유도한다. 이어서 고정된 숫자 예제를 손계산하고, 같은 식을 NumPy로 다시 계산해 소수점 넷째 자리까지 비교한다.

자동미분 라이브러리는 쓰지 않는다. 활성화는 시그모이드, 손실은 이진 교차 엔트로피(BCE)이다.

과제 문장에 정답 라벨의 숫자가 비어 있다. 이 노트북은 **y_true = 1** 로 고정한다.
"""
        ),
        markdown(
            """## 1. 구조와 순전파

열벡터 규약을 쓴다. 은닉층 가중치 \\(W^{(1)}\\)의 각 행이 은닉 유닛 하나이고, 출력층 가중치 \\(W^{(2)}\\)는 길이가 2인 벡터이다.

| 기호 | shape | 의미 |
| --- | --- | --- |
| \\(x\\) | (2,) | 입력 |
| \\(W^{(1)}\\) | (2, 2) | 입력 → 은닉 |
| \\(b^{(1)}\\) | (2,) | 은닉 편향 |
| \\(z^{(1)}\\) | (2,) | 은닉 로짓 |
| \\(a^{(1)}\\) | (2,) | 은닉 활성화 |
| \\(W^{(2)}\\) | (2,) | 은닉 → 출력 |
| \\(b^{(2)}\\) | () | 출력 편향 |
| \\(z^{(2)}\\) | () | 출력 로짓 |
| \\(\\hat{y}\\) | () | 예측 확률 |
| \\(y\\) | () | 정답 0 또는 1 |

시그모이드와 손실은 다음과 같다.

$$
\\sigma(z)=\\frac{1}{1+e^{-z}},\\qquad
\\sigma'(z)=\\sigma(z)\\,(1-\\sigma(z))
$$

$$
L=\\big(y\\log\\hat{y}+(1-y)\\log(1-\\hat{y})\\big)\\text{의 부호를 바꾼 값}
= -\\big(y\\log\\hat{y}+(1-y)\\log(1-\\hat{y})\\big)
$$

순전파는 네 단계다.

$$
z^{(1)}=W^{(1)} x+b^{(1)}
$$

$$
a^{(1)}=\\sigma\\big(z^{(1)}\\big)
$$

$$
z^{(2)}=W^{(2)}\\cdot a^{(1)}+b^{(2)}
$$

$$
\\hat{y}=\\sigma\\big(z^{(2)}\\big)
$$

\\(W^{(1)} x\\)는 행렬-벡터 곱이라 shape이 (2, 2) × (2,) = (2,)이다. \\(W^{(2)}\\cdot a^{(1)}\\)는 내적이라 스칼라가 된다.
"""
        ),
        markdown(
            """## 2. 출력층에서 입력층으로의 역전파

각 단계에서 연쇄 법칙과 텐서 shape을 같이 적는다.

### 2.1 \\(\\partial L/\\partial\\hat{y}\\)  — shape ()

\\(y\\in\\{0,1\\}\\)이고 \\(\\hat{y}\\in(0,1)\\)일 때

$$
\\frac{\\partial L}{\\partial\\hat{y}}
= -\\frac{y}{\\hat{y}}+\\frac{1-y}{1-\\hat{y}}.
$$

\\(y=1\\)이면 \\(-1/\\hat{y}\\), \\(y=0\\)이면 \\(1/(1-\\hat{y})\\)이다.

### 2.2 \\(\\partial L/\\partial z^{(2)}\\)  — shape ()

$$
\\frac{\\partial\\hat{y}}{\\partial z^{(2)}}=\\hat{y}(1-\\hat{y})
$$

$$
\\frac{\\partial L}{\\partial z^{(2)}}
=\\frac{\\partial L}{\\partial\\hat{y}}\\,\\hat{y}(1-\\hat{y})
=\\left(-\\frac{y}{\\hat{y}}+\\frac{1-y}{1-\\hat{y}}\\right)\\hat{y}(1-\\hat{y}).
$$

괄호를 풀면

$$
- y(1-\\hat{y})+(1-y)\\hat{y}
= -y+y\\hat{y}+\\hat{y}-y\\hat{y}
= \\hat{y}-y.
$$

따라서 BCE와 시그모이드를 이으면 \\(\\partial L/\\partial z^{(2)}=\\hat{y}-y\\)이다. 아래 손계산에서는 나누기 전의 식과 이 단순화 결과가 같은지 둘 다 적는다.

### 2.3 \\(\\partial L/\\partial W^{(2)}\\)  — shape (2,)

\\(z^{(2)}=W^{(2)}\\cdot a^{(1)}+b^{(2)}\\)이므로 \\(W^{(2)}\\)에 대한 기울기는 스칼라 기울기에 활성화 벡터를 곱한 것이다.

$$
\\frac{\\partial L}{\\partial W^{(2)}}
=\\frac{\\partial L}{\\partial z^{(2)}}\\, a^{(1)}
\\qquad
()\\times(2,)=(2,)
$$

편향은 \\(\\partial L/\\partial b^{(2)}=\\partial L/\\partial z^{(2)}\\)이고 shape은 ()이다. 과제 필수 목록에는 없지만 순전파에 들어 있으므로 함께 적는다.

### 2.4 \\(\\partial L/\\partial a^{(1)}\\)  — shape (2,)

같은 내적을 \\(a^{(1)}\\) 쪽으로 보면 가중치가 남는다.

$$
\\frac{\\partial L}{\\partial a^{(1)}}
=\\frac{\\partial L}{\\partial z^{(2)}}\\, W^{(2)}
\\qquad
()\\times(2,)=(2,)
$$

### 2.5 \\(\\partial L/\\partial z^{(1)}\\)  — shape (2,)

은닉 활성화는 성분마다 시그모이드이다. 야코비안은 대각행렬 \\(\\mathrm{diag}\\big(a^{(1)}\\odot(1-a^{(1)})\\big)\\)이므로 벡터 기울기는 원소별 곱이다.

$$
\\frac{\\partial L}{\\partial z^{(1)}}
=\\frac{\\partial L}{\\partial a^{(1)}}
\\odot a^{(1)}\\odot\\big(1-a^{(1)}\\big)
\\qquad (2,)
$$

\\(\\partial L/\\partial b^{(1)}\\)도 이 벡터와 같다.

### 2.6 \\(\\partial L/\\partial W^{(1)}\\)  — shape (2, 2)

\\(z^{(1)}=W^{(1)} x+b^{(1)}\\)에서 \\(z^{(1)}\\)의 기울기를 \\(g\\)라고 하면

$$
\\frac{\\partial L}{\\partial W^{(1)}}=g\\, x^{\\top}
=\\frac{\\partial L}{\\partial z^{(1)}}\\, x^{\\top}.
$$

shape은 (2, 1) × (1, 2) = (2, 2)이다. \\(x=(1,0)\\)이면 첫 번째 열만 남고 두 번째 열은 0이다. 입력이 0인 가중치로는 이번 샘플의 손실이 바뀌지 않기 때문이다.
"""
        ),
        markdown(
            """## 3. 고정 예제의 손계산

### 입력 체크포인트

| 텐서 | shape | 값 |
| --- | --- | --- |
| \\(x\\) | (2,) | \\([1,\\ 0]\\) |
| \\(W^{(1)}\\) | (2, 2) | \\([[0.1,\\ 0.2],\\ [0.3,\\ 0.4]]\\) |
| \\(b^{(1)}\\) | (2,) | \\([0,\\ 0]\\) |
| \\(W^{(2)}\\) | (2,) | \\([0.5,\\ 0.6]\\) |
| \\(b^{(2)}\\) | () | \\(0\\) |
| \\(y\\) | () | \\(1\\) |

### 순전파 체크포인트

**\\(z^{(1)}\\), shape (2,)**

$$
z^{(1)}_1=0.1\\cdot 1+0.2\\cdot 0+0=0.1
$$

$$
z^{(1)}_2=0.3\\cdot 1+0.4\\cdot 0+0=0.3
$$

$$
z^{(1)}=[0.1,\\ 0.3]
$$

**\\(a^{(1)}\\), shape (2,)**

$$
e^{-0.1}=0.904837418,\\quad
\\sigma(0.1)=\\frac{1}{1.904837418}=0.524979187
$$

$$
e^{-0.3}=0.740818221,\\quad
\\sigma(0.3)=\\frac{1}{1.740818221}=0.574442517
$$

$$
a^{(1)}=[0.524979187,\\ 0.574442517]
$$

**\\(z^{(2)}\\), shape ()**

$$
z^{(2)}=0.5\\cdot 0.524979187+0.6\\cdot 0.574442517+0
$$

$$
=0.262489594+0.344665510=0.607155104
$$

**\\(\\hat{y}\\), shape ()**

$$
e^{-0.607155104}=0.544947\\text{ 부근},\\quad
\\hat{y}=\\sigma(0.607155104)=0.647291570
$$

정답이 1이므로 손실은 \\(L=-\\log\\hat{y}=0.434958437\\)이다. 필수 체크포인트는 \\(z^{(1)}, a^{(1)}, z^{(2)}, \\hat{y}\\) 네 개다.

### 역전파 체크포인트

**\\(\\partial L/\\partial\\hat{y}\\), shape ()**

$$
\\frac{\\partial L}{\\partial\\hat{y}}=-\\frac{1}{0.647291570}=-1.544898847
$$

**\\(\\partial L/\\partial z^{(2)}\\), shape ()**

$$
\\hat{y}(1-\\hat{y})=0.647291570\\cdot 0.352708430=0.228308
$$

$$
\\frac{\\partial L}{\\partial\\hat{y}}\\,\\hat{y}(1-\\hat{y})
=-1.544898847\\cdot 0.647291570\\cdot 0.352708430
=-0.352708430
$$

단순화 \\(\\hat{y}-y=0.647291570-1=-0.352708430\\)과 같다.

**\\(\\partial L/\\partial W^{(2)}\\), shape (2,)**

$$
(-0.352708430)\\,[0.524979187,\\ 0.574442517]
=[-0.185164585,\\ -0.202610718]
$$

**\\(\\partial L/\\partial a^{(1)}\\), shape (2,)**

$$
(-0.352708430)\\,[0.5,\\ 0.6]
=[-0.176354215,\\ -0.211625058]
$$

**\\(\\partial L/\\partial z^{(1)}\\), shape (2,)**

시그모이드 도함수:

$$
a^{(1)}\\odot(1-a^{(1)})
=[0.249376040,\\ 0.244458312]
$$

$$
\\frac{\\partial L}{\\partial z^{(1)}}
=[-0.176354215\\cdot 0.249376040,\\ 
-0.211625058\\cdot 0.244458312]
=[-0.043978516,\\ -0.051733504]
$$

**\\(\\partial L/\\partial W^{(1)}\\), shape (2, 2)**

\\(x=(1,0)\\)과의 외적이다. 두 번째 열은 0이다.

$$
\\frac{\\partial L}{\\partial W^{(1)}}
=
\\begin{bmatrix}
-0.043978516 & 0\\\\
-0.051733504 & 0
\\end{bmatrix}
$$

### 소수점 넷째 자리 기준값

비교에 쓰는 값은 위에서 구한 수를 소수 넷째 자리에서 반올림한 결과이다.

| 텐서 | shape | 반올림 값 |
| --- | --- | --- |
| \\(z^{(1)}\\) | (2,) | [0.1000, 0.3000] |
| \\(a^{(1)}\\) | (2,) | [0.5250, 0.5744] |
| \\(z^{(2)}\\) | () | 0.6072 |
| \\(\\hat{y}\\) | () | 0.6473 |
| \\(\\partial L/\\partial\\hat{y}\\) | () | -1.5449 |
| \\(\\partial L/\\partial z^{(2)}\\) | () | -0.3527 |
| \\(\\partial L/\\partial W^{(2)}\\) | (2,) | [-0.1852, -0.2026] |
| \\(\\partial L/\\partial a^{(1)}\\) | (2,) | [-0.1764, -0.2116] |
| \\(\\partial L/\\partial z^{(1)}\\) | (2,) | [-0.0440, -0.0517] |
| \\(\\partial L/\\partial W^{(1)}\\) | (2, 2) | [[-0.0440, 0.0000], [-0.0517, 0.0000]] |
"""
        ),
        code(
            """import sys
from pathlib import Path

import numpy as np

ROOT = Path.cwd().resolve()
if not (ROOT / "src").exists():
    ROOT = ROOT.parent
sys.path.insert(0, str(ROOT))
np.random.seed(42)


def sigmoid(z):
    \"\"\"시그모이드 σ(z) = 1 / (1 + exp(-z)).\"\"\"
    return 1.0 / (1.0 + np.exp(-z))


# shape: x (2,), W1 (2, 2), b1 (2,), W2 (2,), b2 (), y ()
x = np.array([1.0, 0.0])
W1 = np.array([[0.1, 0.2], [0.3, 0.4]])
b1 = np.array([0.0, 0.0])
W2 = np.array([0.5, 0.6])
b2 = 0.0
y_true = 1.0

# 순전파. z1 = W1 @ x + b1
z1 = W1 @ x + b1          # (2,)
a1 = sigmoid(z1)          # (2,)
z2 = float(W2 @ a1 + b2)  # ()
y_pred = float(sigmoid(z2))  # ()

# 역전파. BCE 미분 후 시그모이드 도함수를 곱한다.
dL_dy = -y_true / y_pred + (1.0 - y_true) / (1.0 - y_pred)  # ()
dL_dz2 = dL_dy * y_pred * (1.0 - y_pred)  # ()
dL_dz2_simplified = y_pred - y_true       # () , ŷ - y
dL_dW2 = dL_dz2 * a1                      # (2,)
dL_da1 = dL_dz2 * W2                      # (2,)
dL_dz1 = dL_da1 * a1 * (1.0 - a1)         # (2,)
dL_dW1 = np.outer(dL_dz1, x)              # (2, 2)

hand = {
    "z1": np.array([0.1000, 0.3000]),
    "a1": np.array([0.5250, 0.5744]),
    "z2": np.array(0.6072),
    "y_pred": np.array(0.6473),
    "dL_dy": np.array(-1.5449),
    "dL_dz2": np.array(-0.3527),
    "dL_dW2": np.array([-0.1852, -0.2026]),
    "dL_da1": np.array([-0.1764, -0.2116]),
    "dL_dz1": np.array([-0.0440, -0.0517]),
    "dL_dW1": np.array([[-0.0440, 0.0000], [-0.0517, 0.0000]]),
}
computed = {
    "z1": z1,
    "a1": a1,
    "z2": np.array(z2),
    "y_pred": np.array(y_pred),
    "dL_dy": np.array(dL_dy),
    "dL_dz2": np.array(dL_dz2),
    "dL_dW2": dL_dW2,
    "dL_da1": dL_da1,
    "dL_dz1": dL_dz1,
    "dL_dW1": dL_dW1,
}
shapes = {
    "x": x.shape,
    "W1": W1.shape,
    "b1": b1.shape,
    "z1": z1.shape,
    "a1": a1.shape,
    "W2": W2.shape,
    "z2": (),
    "y_pred": (),
    "dL_dy": (),
    "dL_dz2": (),
    "dL_dW2": dL_dW2.shape,
    "dL_da1": dL_da1.shape,
    "dL_dz1": dL_dz1.shape,
    "dL_dW1": dL_dW1.shape,
}

print("shape")
for name, shape in shapes.items():
    print(f"  {name:8s} {shape}")
print()
print(f"∂L/∂z2 직접 계산 {dL_dz2:.10f}")
print(f"∂L/∂z2 = y_pred - y {dL_dz2_simplified:.10f}")
print()
print(f"{'이름':12s} {'NumPy 원값':22s} {'소수 4자리':22s} {'손계산':22s}")
for name, expected in hand.items():
    raw = computed[name]
    got = np.round(raw, 4)
    assert np.array_equal(got, expected), (name, got, expected)
    print(f"{name:12s} {np.array2string(raw, precision=6):22s} {np.array2string(got, precision=4):22s} {np.array2string(expected, precision=4):22s}")
print()
print("소수점 4자리까지 손계산과 일치한다.")
"""
        ),
    ]
)


PROBABILITY = notebook(
    [
        markdown(
            """# 손실 함수와 최대우도

정규분포와 베르누이 분포를 그린 뒤, 자주 쓰는 손실이 특정 분포의 최대우도추정(MLE)과 같은 최적화 문제임을 수식으로 연결한다.

표기 \\(N(\\mu,\\sigma^2)\\)에서 둘째 인자는 분산이다. \\(N(2, 0.5)\\)는 평균 2, 분산 0.5, 표준편차 \\(\\sqrt{0.5}\\)이다.

재현을 위해 난수 시드는 42로 고정한다. NumPy만 계산에 쓰고, 그림은 Matplotlib과 Seaborn으로 저장한다.
"""
        ),
        code(
            """import sys
from pathlib import Path

import numpy as np

ROOT = Path.cwd().resolve()
if not (ROOT / "src").exists():
    ROOT = ROOT.parent
sys.path.insert(0, str(ROOT))
np.random.seed(42)

from src.probability import plot_bernoulli_pmfs, plot_normal_pdfs, softmax_total_gap
from src.calculus import softmax

plot_normal_pdfs(ROOT / "outputs" / "normal_pdf.png")
plot_bernoulli_pmfs(ROOT / "outputs" / "bernoulli_pmf.png")

logits = np.random.randn(5)
probabilities = softmax(logits)
gap = abs(float(probabilities.sum()) - 1.0)
assert gap < 1e-6, gap
print("소프트맥스 입력", np.array2string(logits, precision=4))
print("소프트맥스 출력", np.array2string(probabilities, precision=6))
print("합", float(probabilities.sum()), "1과의 차이", gap)
print("시드 42 기본 벡터의 차이", softmax_total_gap())
"""
        ),
        markdown(
            """## 정규분포 PDF와 베르누이 PMF

정규분포의 밀도는

$$
\\phi(x;\\mu,\\sigma^2)
=\\frac{1}{\\sqrt{2\\pi\\sigma^2}}
\\exp\\left(-\\frac{(x-\\mu)^2}{2\\sigma^2}\\right).
$$

위 코드가 `outputs/normal_pdf.png`에 \\(N(0,1)\\)과 \\(N(2,0.5)\\)를 함께 그린다. 평균이 오른쪽으로 옮겨지고 분산이 1에서 0.5로 줄면 봉우리가 오른쪽으로 이동하면서 좁아진다.

베르누이 분포 \\(B(p)\\)는 두 점만 갖는다.

$$
P(K=1)=p,\\qquad P(K=0)=1-p.
$$

`outputs/bernoulli_pmf.png`는 \\(B(0.3)\\)과 \\(B(0.7)\\)이다. 성공 확률이 0.5를 넘으면 질량이 \\(k=1\\) 쪽으로 기울어진다.

소프트맥스는 로짓 \\(z\\)를 범주 확률로 바꾼다.

$$
\\mathrm{softmax}(z)_i=\\frac{e^{z_i}}{\\sum_j e^{z_j}}.
$$

분모로 나누므로 성분의 합은 1이고, 위 셀에서 \\(|\\sum_i p_i-1|<10^{-6}\\)을 확인한다. 구현은 최댓값 \\(m=\\max_j z_j\\)를 빼서 \\(e^{z_i-m}\\)을 쓰지만, 분자와 분모에 \\(e^{-m}\\)이 같이 들어가 값은 같다.
"""
        ),
        markdown(
            """## MSE 최소화는 정규분포 가정에서의 MLE

입력 \\(x_i\\)가 주어졌을 때 관측이 조건부 정규분포를 따른다고 가정한다.

$$
y_i\\mid x_i\\sim N\\big(\\mu_i,\\sigma^2\\big),
\\qquad
\\mu_i=f_\\theta(x_i).
$$

분산 \\(\\sigma^2\\)는 \\(\\theta\\)와 무관한 양수 상수로 둔다. 표본이 독립이면 우도는

$$
L(\\theta)
=\\prod_{i=1}^{n}
\\frac{1}{\\sqrt{2\\pi\\sigma^2}}
\\exp\\left(-\\frac{(y_i-\\mu_i)^2}{2\\sigma^2}\\right).
$$

로그를 취하면

$$
\\ell(\\theta)
=-\\frac{n}{2}\\log(2\\pi\\sigma^2)
-\\frac{1}{2\\sigma^2}\\sum_{i=1}^{n}(y_i-\\mu_i)^2.
$$

첫 항은 \\(\\theta\\)를 포함하지 않는다. 둘째 항의 계수 \\(1/(2\\sigma^2)\\)는 양수이므로, \\(\\ell(\\theta)\\)를 최대로 만드는 \\(\\theta\\)는 다음을 최소로 만드는 \\(\\theta\\)와 같다.

$$
\\sum_{i=1}^{n}(y_i-f_\\theta(x_i))^2
$$

평균제곱오차는 이 제곱합을 \\(n\\)으로 나눈 것이다.

$$
\\mathrm{MSE}(\\theta)=\\frac{1}{n}\\sum_{i=1}^{n}(y_i-f_\\theta(x_i))^2.
$$

\\(1/n\\)도 양수 상수이므로

$$
\\arg\\min_\\theta\\ \\mathrm{MSE}(\\theta)
=\\arg\\max_\\theta\\ \\ell(\\theta).
$$

즉 가우시안 잡음 가정에서 평균을 신경망 예측으로 두면, MSE를 줄이는 일과 로그우도를 키우는 일은 같은 매개변수에서 끝난다. 분산을 함께 추정하면 로그우도에 \\(\\log\\sigma^2\\) 항이 남아 MSE와 완전히 같은 식은 아니지만, \\(\\sigma^2\\)를 고정하면 둘의 최적 \\(\\theta\\)는 같다.

다음 셀은 이 항등식을 숫자로 확인한다. \\(\\mu\\)가 바뀌어도 \\(\\ell+\\mathrm{SSE}/(2\\sigma^2)\\)는 상수이다.
"""
        ),
        code(
            """# ℓ(θ) + SSE / (2 σ^2) 는 μ와 무관한 상수여야 한다.
sigma2 = 0.5
y = np.array([0.0, 1.2, -0.4, 0.7])
predictions = [
    np.array([0.0, 0.0, 0.0, 0.0]),
    np.array([0.2, 1.0, -0.5, 0.4]),
    y.copy(),
]
constant_term = -0.5 * len(y) * np.log(2.0 * np.pi * sigma2)
anchors = []
for mu in predictions:
    sse = float(np.sum((y - mu) ** 2))
    log_likelihood = constant_term - sse / (2.0 * sigma2)
    anchors.append(log_likelihood + sse / (2.0 * sigma2))
    print(f"SSE={sse:.6f}  loglik={log_likelihood:.6f}  loglik+SSE/(2σ²)={anchors[-1]:.6f}")
assert np.allclose(anchors, anchors[0])
print("로그우도에서 제곱합 항을 빼면 예측값과 무관한 상수가 남는다.")
"""
        ),
        markdown(
            """## Cross-Entropy 최소화는 베르누이·범주 분포 가정에서의 MLE

### 베르누이와 이진 교차 엔트로피

정답 \\(y_i\\in\\{0,1\\}\\)이고, 모델이 성공 확률 \\(\\hat{y}_i\\in(0,1)\\)를 낸다고 하자.

$$
P(y_i\\mid x_i)=\\hat{y}_i^{y_i}(1-\\hat{y}_i)^{1-y_i}.
$$

독립 표본의 로그우도는

$$
\\ell(\\theta)
=\\sum_{i=1}^{n}\\Big(y_i\\log\\hat{y}_i+(1-y_i)\\log(1-\\hat{y}_i)\\Big).
$$

이진 교차 엔트로피는 이 식의 부호를 평균 낸 것이다.

$$
\\mathrm{BCE}(\\theta)
=-\\frac{1}{n}\\sum_{i=1}^{n}\\Big(y_i\\log\\hat{y}_i+(1-y_i)\\log(1-\\hat{y}_i)\\Big).
$$

따라서 \\(\\mathrm{BCE}\\)를 최소화하는 \\(\\theta\\)는 베르누이 로그우도를 최대화하는 \\(\\theta\\)와 같다. 앞 노트북의 손실 \\(L=-(y\\log\\hat{y}+(1-y)\\log(1-\\hat{y}))\\)는 표본 하나짜리 BCE이다.

### 범주 분포와 교차 엔트로피

클래스가 \\(K\\)개이고 정답이 원-핫 벡터 \\(y_i\\)이면

$$
P(y_i\\mid x_i)=\\prod_{k=1}^{K} p_{i,k}^{y_{i,k}},
\\qquad
p_i=\\mathrm{softmax}(z_i).
$$

로그우도는

$$
\\ell(\\theta)=\\sum_{i=1}^{n}\\sum_{k=1}^{K} y_{i,k}\\log p_{i,k}.
$$

범주 교차 엔트로피는

$$
\\mathrm{CE}(\\theta)
=-\\frac{1}{n}\\sum_{i=1}^{n}\\sum_{k=1}^{K} y_{i,k}\\log p_{i,k}.
$$

부호와 양의 상수 \\(1/n\\)만 다르므로

$$
\\arg\\min_\\theta\\ \\mathrm{CE}(\\theta)
=\\arg\\max_\\theta\\ \\ell(\\theta).
$$

소프트맥스 출력은 음이 아니고 합이 1이라 범주 분포의 확률벡터로 쓸 수 있다. 위에서 합이 1에서 \\(10^{-6}\\)보다 덜 어긋남을 확인한 것은 이 확률 조건을 수치로 고정한 것이다.

정리하면, MSE는 조건부 정규분포의 평균을 맞추는 MLE이고, 교차 엔트로피는 베르누이 또는 범주 분포의 확률을 맞추는 MLE이다. 손실의 모양은 어떤 분포로 관측을 설명할지 고른 결과이다.
"""
        ),
    ]
)


def main() -> None:
    """두 노트북 파일을 쓴다."""
    notebook_dir = ROOT / "notebooks"
    notebook_dir.mkdir(parents=True, exist_ok=True)
    (notebook_dir / "backprop_derivation.ipynb").write_text(
        json.dumps(BACKPROP, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    (notebook_dir / "probability_loss.ipynb").write_text(
        json.dumps(PROBABILITY, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
