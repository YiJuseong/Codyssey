"""미적분: 중심차분 수치 미분, 기울기 장 시각화, 소프트맥스.

자동미분 라이브러리는 사용하지 않는다.
소프트맥스는 확률 노트북의 정규화 조건을 코드로 확인하려고 이 모듈에 둔다.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from src.plot_style import configure_matplotlib, ensure_parent

configure_matplotlib()


def central_difference(function, x: float, h: float = 1e-6) -> float:
    """스칼라 함수의 도함수를 중심차분으로 근사한다.

    f'(x) ≈ (f(x+h) - f(x-h)) / (2h)

    오차의 주도항은 O(h^2)이다. f(x)=x^2처럼 3차 이상 도함수가 0인 함수에서는
    절단오차가 없고, 남는 차이는 부동소수 연산에서 온다.
    """
    if h <= 0.0:
        raise ValueError("간격 h는 양수여야 한다.")
    point = float(x)
    return float((function(point + h) - function(point - h)) / (2.0 * h))


def numerical_gradient(function, point: np.ndarray, h: float = 1e-6) -> np.ndarray:
    """다변수 함수의 기울기를 좌표별 중심차분으로 구한다.

    ∂f/∂x_i ≈ (f(x+h e_i) - f(x-h e_i)) / (2h)
    """
    if h <= 0.0:
        raise ValueError("간격 h는 양수여야 한다.")
    vector = np.asarray(point, dtype=float).reshape(-1) # 매개변수로 받은 자료구조를 1차원 벡터 배열로 변환
    gradient = np.zeros_like(vector) # 0으로 채워진 매개변수와 크기와 타입이 같은 자료구조 생성
    for index in range(vector.size):
        forward = vector.copy()
        backward = vector.copy()
        forward[index] += h
        backward[index] -= h
        gradient[index] = (function(forward) - function(backward)) / (2.0 * h)
    return gradient


def softmax(logits: np.ndarray) -> np.ndarray:
    """소프트맥스 확률 벡터를 반환한다.

    softmax(z)_i = exp(z_i) / Σ_j exp(z_j)

    최대 로짓을 빼서 exp 오버플로를 피한다. 이 평행이동은 분모와 분자에
    같은 상수를 곱하므로 값을 바꾸지 않는다. 출력 성분의 합은 1이다.
    """
    values = np.asarray(logits, dtype=float).reshape(-1)
    shifted = values - np.max(values) # 배열중 최대값을 각 원소에 모두 뺴기 연산
    exponential = np.exp(shifted) # 각 원소의 지수함수값 연산
    total = np.sum(exponential)
    if total == 0.0:
        raise ValueError("소프트맥스 분모가 0이다.")
    return exponential / total


def quadratic_bowl(point: np.ndarray) -> float:
    """f(x, y) = x^2 + y^2."""
    vector = np.asarray(point, dtype=float).reshape(-1)
    return float(np.dot(vector, vector)) # 벡터의 내적 또는 행렬곱 연산


def analytical_gradient_quadratic_bowl(point: np.ndarray) -> np.ndarray:
    """∇(x^2 + y^2) = (2x, 2y)."""
    return 2.0 * np.asarray(point, dtype=float)


def plot_gradient_field(
    save_path: str | Path = "outputs/gradient_contour.png",
    grid_limit: float = 3.0,
) -> float:
    """f(x, y)=x^2+y^2의 등고선과 기울기 화살표를 한 Figure에 저장한다.

    등고선은 원이고, 기울기 (2x, 2y)는 반지름 방향이다. 따라서 화살표는
    등고선에 수직이다. 반환값은 격자점에서 |단위 기울기 · 접선|의 최댓값이다.
    접선은 (-y, x)이고, 이 값이 0에 가까우면 수직이다.
    """
    coordinates = np.linspace(-grid_limit, grid_limit, 200) # -3부터 3까지 균일한 범위로 200개 원소로 나눠서 벡터 배열 생성
    x_grid, y_grid = np.meshgrid(coordinates, coordinates) # 1차원 벡터를 2차원 행렬로 변환
    values = x_grid ** 2 + y_grid ** 2 # 200x200 두 행렬의 각 원소의 제곱합을 원소로 갖는 2차원 행렬 생성

    sample_axis = np.array([-2.0, -1.0, 0.0, 1.0, 2.0])
    sample_x, sample_y = np.meshgrid(sample_axis, sample_axis)
    sample_x = sample_x.ravel()
    sample_y = sample_y.ravel()
    keep = np.logical_not((sample_x == 0.0) & (sample_y == 0.0))
    sample_x = sample_x[keep]
    sample_y = sample_y[keep] # 원점에서 크기가 0이 되어 나중에 분모가 0이 되는 에러예외 처리
    grad_x = 2.0 * sample_x
    grad_y = 2.0 * sample_y # 각 점의 기울기 계산

    tangent_x = -sample_y
    tangent_y = sample_x # 접선 벡터 좌표 계산
    grad_norm = np.hypot(grad_x, grad_y) # 벡터 크기 계산
    tangent_norm = np.hypot(tangent_x, tangent_y)
    alignment = np.abs(
        (grad_x / grad_norm) * (tangent_x / tangent_norm)
        + (grad_y / grad_norm) * (tangent_y / tangent_norm)
    ) # 두 벡터의 내적계산
    max_alignment = float(np.max(alignment))

    figure, axis = plt.subplots(figsize=(6.6, 6.2))
    contour = axis.contour(x_grid, y_grid, values, levels=8, cmap="Blues")
    axis.clabel(contour, inline=True, fontsize=8, fmt="%.0f")
    axis.quiver(
        sample_x,
        sample_y,
        grad_x,
        grad_y,
        angles="xy",
        scale_units="xy",
        scale=8.0,
        color="#d62728",
        width=0.005,
        label=r"$\nabla f=(2x,\ 2y)$",
    )
    axis.set_aspect("equal", adjustable="box")
    axis.set_xlabel("x")
    axis.set_ylabel("y")
    axis.set_title(r"등고선과 기울기: $f(x,y)=x^2+y^2$")
    axis.legend(loc="upper right")
    axis.text(
        0.02,
        0.02,
        f"단위 기울기와 접선의 내적 최댓값 {max_alignment:.1e}\n(0이면 화살표가 등고선에 수직)",
        transform=axis.transAxes,
        va="bottom",
        fontsize=8,
        bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.9},
    )
    figure.tight_layout()
    ensure_parent(save_path)
    figure.savefig(save_path)
    plt.close(figure)
    return max_alignment
