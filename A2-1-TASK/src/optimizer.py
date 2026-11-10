"""최적화: Vanilla Gradient Descent와 Momentum.

갱신식은 매개변수를 열벡터 θ로 두고 다음과 같다.

Vanilla GD:

    θ <- θ - η ∇f(θ)

Momentum (Polyak, PyTorch SGD의 momentum과 같은 형태):

    v <- β v + ∇f(θ)
    θ <- θ - η v

v의 초깃값은 0이다. β=0이면 Vanilla GD와 같다.
자동미분은 쓰지 않고, 기울기는 호출하는 쪽에서 넘긴다.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from src.calculus import quadratic_bowl  # f(x, y) = x^2 + y^2, calculus.py와 공유
from src.plot_style import configure_matplotlib, ensure_parent

configure_matplotlib()


class VanillaGD:
    """학습률만 사용하는 경사하강법.

    θ_{t+1} = θ_t - η ∇f(θ_t)
    """

    def __init__(self, lr: float = 0.1):
        """학습률 η를 저장한다."""
        if lr <= 0.0:
            raise ValueError("학습률은 양수여야 한다.")
        self.lr = float(lr)

    def step(self, theta: np.ndarray, grad: np.ndarray) -> np.ndarray:
        """기울기 한 번으로 매개변수를 갱신한다."""
        theta = np.asarray(theta, dtype=float)
        grad = np.asarray(grad, dtype=float)
        return theta - self.lr * grad


class Momentum:
    """속도 항을 누적하는 Momentum 옵티마이저.

    v_{t+1} = β v_t + ∇f(θ_t)
    θ_{t+1} = θ_t - η v_{t+1}

    속도는 인스턴스에 유지된다. 새 경로를 시작할 때는 reset()을 호출한다.
    """

    def __init__(self, lr: float = 0.1, beta: float = 0.9):
        """학습률 η와 감쇠 계수 β를 저장한다."""
        if lr <= 0.0:
            raise ValueError("학습률은 양수여야 한다.")
        if not 0.0 <= beta < 1.0:
            raise ValueError("beta는 [0, 1) 구간이어야 한다.")
        self.lr = float(lr)
        self.beta = float(beta)
        self.velocity: np.ndarray | None = None

    def reset(self) -> None:
        """누적 속도를 지운다."""
        self.velocity = None

    def step(self, theta: np.ndarray, grad: np.ndarray) -> np.ndarray:
        """속도에 기울기를 더한 뒤 매개변수를 옮긴다."""
        theta = np.asarray(theta, dtype=float)
        grad = np.asarray(grad, dtype=float)
        if self.velocity is None or self.velocity.shape != theta.shape:
            self.velocity = np.zeros_like(theta)
        self.velocity = self.beta * self.velocity + grad
        return theta - self.lr * self.velocity


def grad_quadratic_bowl(theta: np.ndarray) -> np.ndarray:
    """∇(x^2 + y^2) = (2x, 2y)."""
    return 2.0 * np.asarray(theta, dtype=float)


def grad_ellipse(theta: np.ndarray) -> np.ndarray:
    """∇(x^2 + 10 y^2) = (2x, 20y)."""
    vector = np.asarray(theta, dtype=float)
    return np.array([2.0 * vector[0], 20.0 * vector[1]], dtype=float)


def ellipse(theta: np.ndarray) -> float:
    """f(x, y) = x^2 + 10 y^2."""
    vector = np.asarray(theta, dtype=float)
    return float(vector[0] ** 2 + 10.0 * vector[1] ** 2)


def run_optimizer(optimizer, grad_fn, theta0: np.ndarray, n_steps: int) -> np.ndarray:
    """옵티마이저를 n_steps번 적용하고 경로를 반환한다.

    반환 shape은 (n_steps + 1, dim)이고 0번 행이 시작점이다.
    Momentum이면 경로를 시작하기 전에 속도를 초기화한다.
    """
    if isinstance(optimizer, Momentum):
        optimizer.reset()
    theta = np.asarray(theta0, dtype=float).copy()
    path = [theta.copy()]
    for _ in range(n_steps):
        theta = optimizer.step(theta, grad_fn(theta))
        path.append(np.asarray(theta, dtype=float).copy())
    return np.vstack(path)


def path_radius(path: np.ndarray) -> np.ndarray:
    """각 시점의 원점 거리 ||θ||를 반환한다."""
    return np.linalg.norm(path, axis=1)


def _contour_background(axis, function, xlim: tuple[float, float], ylim: tuple[float, float]) -> None:
    """등고선을 축에 그린다."""
    x_coord = np.linspace(xlim[0], xlim[1], 250)
    y_coord = np.linspace(ylim[0], ylim[1], 250)
    x_grid, y_grid = np.meshgrid(x_coord, y_coord)
    values = np.vectorize(lambda x_value, y_value: function(np.array([x_value, y_value])))(
        x_grid, y_grid
    )
    axis.contour(x_grid, y_grid, values, levels=12, cmap="Greys", alpha=0.85)


def plot_convergence_path(
    path: np.ndarray,
    function,
    title: str,
    save_path: str | Path,
    xlim: tuple[float, float],
    ylim: tuple[float, float],
) -> None:
    """등고선 위에 수렴 경로를 점선으로 저장한다."""
    figure, axis = plt.subplots(figsize=(6.4, 5.8))
    _contour_background(axis, function, xlim, ylim)
    axis.plot(path[:, 0], path[:, 1], linestyle="--", color="#1f77b4", linewidth=1.8, label="경로")
    axis.scatter(path[0, 0], path[0, 1], color="#2ca02c", s=36, zorder=3, label="시작")
    axis.scatter(path[-1, 0], path[-1, 1], color="#d62728", s=36, zorder=3, label="끝")
    axis.set_xlim(*xlim)
    axis.set_ylim(*ylim)
    axis.set_aspect("equal", adjustable="box")
    axis.set_xlabel("x")
    axis.set_ylabel("y")
    axis.set_title(title)
    axis.legend(loc="upper right")
    figure.tight_layout()
    ensure_parent(save_path)
    figure.savefig(save_path)
    plt.close(figure)


def plot_optimizer_comparison(
    paths: dict[str, np.ndarray],
    function,
    title: str,
    save_path: str | Path,
    xlim: tuple[float, float],
    ylim: tuple[float, float],
) -> None:
    """여러 옵티마이저 경로를 한 등고선 Figure에 점선으로 겹친다."""
    colors = ("#1f77b4", "#d62728", "#2ca02c", "#9467bd")
    figure, axis = plt.subplots(figsize=(6.8, 5.8))
    _contour_background(axis, function, xlim, ylim)
    for color, (label, path) in zip(colors, paths.items()):
        axis.plot(path[:, 0], path[:, 1], linestyle="--", color=color, linewidth=1.8, label=label)
        axis.scatter(path[0, 0], path[0, 1], color=color, s=28, zorder=3)
        axis.scatter(path[-1, 0], path[-1, 1], color=color, marker="x", s=42, zorder=3)
    axis.set_xlim(*xlim)
    axis.set_ylim(*ylim)
    axis.set_aspect("equal", adjustable="box")
    axis.set_xlabel("x")
    axis.set_ylabel("y")
    axis.set_title(title)
    axis.legend(loc="upper right")
    figure.tight_layout()
    ensure_parent(save_path)
    figure.savefig(save_path)
    plt.close(figure)


def plot_learning_rate_stability(
    grad_fn,
    theta0: np.ndarray,
    learning_rates: tuple[float, ...],
    n_steps: int,
    save_path: str | Path,
    title: str,
) -> dict[float, float]:
    """학습률별 원점 거리를 한 그래프에 그려 발산 여부를 보여 준다.

    f(x,y)=x^2+y^2이고 기울기가 (2x, 2y)이면 갱신은

        θ_{t+1} = (1 - 2η) θ_t

    이다. |1-2η| < 1, 즉 0 < η < 1 이면 원점으로 수렴한다.
    η = 0.5이면 계수가 0이라 한 번에 원점에 닿는다.
    η > 1이면 거리가 기하급수로 커져 발산한다.
    η = 1이면 부호만 바뀌며 같은 거리를 왕복한다.

    Returns:
        학습률별 마지막 원점 거리.
    """
    figure, axis = plt.subplots(figsize=(7.2, 4.8))
    final_radius: dict[float, float] = {}
    for lr in learning_rates:
        path = run_optimizer(VanillaGD(lr=lr), grad_fn, theta0, n_steps)
        radius = path_radius(path)
        final_radius[lr] = float(radius[-1])
        axis.plot(np.arange(radius.shape[0]), radius, linewidth=1.8, label=f"lr={lr:g}")
    axis.set_yscale("log")
    axis.set_xlabel("반복 횟수")
    axis.set_ylabel(r"원점 거리 $||\theta||$")
    axis.set_title(title)
    axis.legend(loc="best")
    axis.grid(True, which="both", alpha=0.3)
    figure.tight_layout()
    ensure_parent(save_path)
    figure.savefig(save_path)
    plt.close(figure)
    return final_radius