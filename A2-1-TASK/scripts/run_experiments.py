"""요구사항 수치 검증과 outputs/ PNG 생성을 한 번에 실행한다.

프로젝트 루트에서 실행한다.

    python scripts/run_experiments.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.calculus import central_difference, plot_gradient_field
from src.linear_algebra import (
    make_grayscale_image,
    plot_rotation,
    plot_scaling,
    plot_shear,
    plot_svd_compression,
    power_iteration,
    reference_dominant_eigenvalue,
    shear_matrix,
    symmetric_demo_matrix,
    unit_circle,
    area_ratio_vs_determinant,
    rotation_matrix,
    scaling_matrix,
)
from src.optimizer import (
    Momentum,
    VanillaGD,
    ellipse,
    grad_ellipse,
    grad_quadratic_bowl,
    path_radius,
    plot_convergence_path,
    plot_learning_rate_stability,
    plot_optimizer_comparison,
    quadratic_bowl,
    run_optimizer,
)
from src.probability import plot_bernoulli_pmfs, plot_normal_pdfs, softmax_total_gap


def sigmoid(z: np.ndarray) -> np.ndarray:
    """σ(z) = 1 / (1 + exp(-z))."""
    return 1.0 / (1.0 + np.exp(-z))


def backprop_example() -> dict[str, np.ndarray]:
    """노트북과 같은 2층 신경망 손계산 예제를 NumPy로 계산한다.

    x=(2,), W1=(2,2), z1=W1 x + b1. y_true=1.
    과제 문장에 정답 라벨 숫자가 비어 있어 1로 고정했다.
    """
    x = np.array([1.0, 0.0])
    w1 = np.array([[0.1, 0.2], [0.3, 0.4]])
    b1 = np.array([0.0, 0.0])
    w2 = np.array([0.5, 0.6])
    b2 = 0.0
    y_true = 1.0

    z1 = w1 @ x + b1
    a1 = sigmoid(z1)
    z2 = float(np.dot(w2, a1) + b2)
    y_pred = float(sigmoid(np.array(z2)))
    d_l_dy = -y_true / y_pred + (1.0 - y_true) / (1.0 - y_pred)
    d_l_dz2 = d_l_dy * y_pred * (1.0 - y_pred)
    d_l_dw2 = d_l_dz2 * a1
    d_l_da1 = d_l_dz2 * w2
    d_l_dz1 = d_l_da1 * a1 * (1.0 - a1)
    d_l_dw1 = np.outer(d_l_dz1, x)
    return {
        "z1": z1,
        "a1": a1,
        "z2": np.array(z2),
        "y_pred": np.array(y_pred),
        "dL_dy": np.array(d_l_dy),
        "dL_dz2": np.array(d_l_dz2),
        "dL_dW2": d_l_dw2,
        "dL_da1": d_l_da1,
        "dL_dz1": d_l_dz1,
        "dL_dW1": d_l_dw1,
    }


def rounded_backprop_matches_hand() -> dict[str, list | float]:
    """손계산을 소수점 넷째 자리에서 반올림한 값과 코드 결과가 같은지 확인한다."""
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
    computed = backprop_example()
    rounded = {}
    for name, expected in hand.items():
        got = np.round(computed[name], 4)
        if not np.array_equal(got, expected):
            raise AssertionError(f"{name} 불일치: 코드 {got}, 손계산 {expected}")
        rounded[name] = got.tolist()
    return rounded


def axis_limits(paths: dict[str, np.ndarray], floor: float) -> tuple[tuple[float, float], tuple[float, float]]:
    """경로가 들어가고, 등고선이 보이도록 축 범위를 잡는다."""
    stacked = np.vstack(list(paths.values()))
    span = max(floor, np.max(np.abs(stacked)) + 0.4)
    return (-span, span), (-span, span)


def main() -> None:
    """그림을 저장하고 수치 조건을 검사한 뒤 지표를 출력한다."""
    np.random.seed(42)
    output_dir = ROOT / "outputs"
    data_dir = ROOT / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    circle = unit_circle(100)
    transforms = {
        "rotation": area_ratio_vs_determinant(rotation_matrix(np.pi / 4.0), circle),
        "scaling": area_ratio_vs_determinant(scaling_matrix(2.0, 0.5), circle),
        "shear": area_ratio_vs_determinant(shear_matrix(1.0), circle),
    }
    plot_rotation(np.pi / 4.0, output_dir / "rotation_unit_circle.png")
    plot_scaling(2.0, 0.5, output_dir / "scaling_unit_circle.png")
    plot_shear(1.0, output_dir / "shear_unit_circle.png")
    for name, stats in transforms.items():
        if stats["relative_error"] > 0.01:
            raise AssertionError(f"{name} 면적비 상대오차 {stats['relative_error']} > 1%")

    matrix = symmetric_demo_matrix(5)
    estimated, _vector = power_iteration(matrix)
    reference = reference_dominant_eigenvalue(matrix)
    eigenvalue_error = abs(estimated - reference) / abs(reference)
    if eigenvalue_error > 0.05:
        raise AssertionError(f"Power Iteration 상대오차 {eigenvalue_error} > 5%")

    image = make_grayscale_image(64)
    np.save(data_dir / "sample_gray_64.npy", image)
    plt.imsave(data_dir / "sample_gray_64.png", image, cmap="gray", vmin=0.0, vmax=1.0)
    svd_errors = plot_svd_compression(image, (10, 50, 100), output_dir / "svd_compression.png")

    derivative = central_difference(lambda value: value ** 2, 3.0)
    derivative_error = abs(derivative - 6.0)
    if derivative_error > 1e-4:
        raise AssertionError(f"수치 미분 오차 {derivative_error} > 1e-4")
    gradient_alignment = plot_gradient_field(output_dir / "gradient_contour.png")
    if gradient_alignment > 1e-8:
        raise AssertionError("기울기 화살표가 등고선 접선과 수직이 아니다.")

    start_bowl = np.array([4.0, 4.0])
    vanilla_bowl = run_optimizer(VanillaGD(lr=0.1), grad_quadratic_bowl, start_bowl, 100)
    momentum_bowl = run_optimizer(Momentum(lr=0.1, beta=0.9), grad_quadratic_bowl, start_bowl, 100)
    vanilla_radius = float(path_radius(vanilla_bowl)[-1])
    if vanilla_radius > 0.1:
        raise AssertionError(f"Vanilla GD 최종 반경 {vanilla_radius} > 0.1")
    bowl_paths = {"Vanilla GD (lr=0.1)": vanilla_bowl, "Momentum (β=0.9, lr=0.1)": momentum_bowl}
    bowl_limits = axis_limits(bowl_paths, floor=4.5)
    plot_convergence_path(
        vanilla_bowl,
        quadratic_bowl,
        r"Vanilla GD, $f=x^2+y^2$, lr=0.1, 100회",
        output_dir / "gd_convergence_bowl.png",
        *bowl_limits,
    )
    plot_optimizer_comparison(
        bowl_paths,
        quadratic_bowl,
        r"Vanilla GD와 Momentum, $f=x^2+y^2$",
        output_dir / "gd_vs_momentum_bowl.png",
        *bowl_limits,
    )
    stability = plot_learning_rate_stability(
        grad_quadratic_bowl,
        start_bowl,
        (0.1, 0.5, 1.0, 1.2),
        12,
        output_dir / "gd_divergence_bowl.png",
        r"$f=x^2+y^2$: $\theta\leftarrow(1-2\eta)\theta$. $\eta>1$이면 발산",
    )
    if stability[0.5] > 1e-8:
        raise AssertionError("lr=0.5는 이 이차함수에서 한 스텝에 원점에 도달해야 한다.")
    if stability[1.2] <= float(np.linalg.norm(start_bowl)):
        raise AssertionError("lr=1.2에서 경로가 발산해야 한다.")

    start_ellipse = np.array([3.0, 1.5])
    vanilla_ellipse = run_optimizer(VanillaGD(lr=0.1), grad_ellipse, start_ellipse, 80)
    momentum_ellipse = run_optimizer(Momentum(lr=0.1, beta=0.9), grad_ellipse, start_ellipse, 80)
    vanilla_ellipse_radius = float(path_radius(vanilla_ellipse)[-1])
    momentum_ellipse_radius = float(path_radius(momentum_ellipse)[-1])
    if momentum_ellipse_radius >= vanilla_ellipse_radius:
        raise AssertionError("타원 함수에서 Momentum 최종 거리가 Vanilla보다 작아야 한다.")
    if momentum_ellipse_radius > 0.1:
        raise AssertionError("Momentum이 타원 함수에서 반경 0.1 안으로 들어와야 한다.")
    ellipse_paths = {
        "Vanilla GD (lr=0.1)": vanilla_ellipse,
        "Momentum (β=0.9, lr=0.1)": momentum_ellipse,
    }
    ellipse_limits = axis_limits(ellipse_paths, floor=3.2)
    plot_optimizer_comparison(
        ellipse_paths,
        ellipse,
        r"Vanilla GD와 Momentum, $f=x^2+10y^2$",
        output_dir / "gd_vs_momentum_ellipse.png",
        *ellipse_limits,
    )

    plot_normal_pdfs(output_dir / "normal_pdf.png")
    plot_bernoulli_pmfs(output_dir / "bernoulli_pmf.png")
    softmax_gap = softmax_total_gap()
    if softmax_gap > 1e-6:
        raise AssertionError(f"소프트맥스 합 오차 {softmax_gap} > 1e-6")

    backprop = rounded_backprop_matches_hand()
    metrics = {
        "area_relative_error": {name: stats["relative_error"] for name, stats in transforms.items()},
        "area_ratio": {name: stats["area_ratio"] for name, stats in transforms.items()},
        "determinant": {name: stats["determinant"] for name, stats in transforms.items()},
        "power_iteration_eigenvalue": estimated,
        "reference_eigenvalue": reference,
        "power_iteration_relative_error": eigenvalue_error,
        "central_difference_at_3": derivative,
        "central_difference_abs_error": derivative_error,
        "gradient_tangent_dot_max": gradient_alignment,
        "vanilla_gd_radius_100": vanilla_radius,
        "momentum_bowl_radius_100": float(path_radius(momentum_bowl)[-1]),
        "learning_rate_final_radius": {str(lr): radius for lr, radius in stability.items()},
        "ellipse_vanilla_radius_80": vanilla_ellipse_radius,
        "ellipse_momentum_radius_80": momentum_ellipse_radius,
        "svd_relative_frobenius": svd_errors,
        "softmax_gap": softmax_gap,
        "backprop_rounded": backprop,
    }
    metrics_path = output_dir / "metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(metrics, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
