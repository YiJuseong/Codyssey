"""확률 분포 시각화.

수식 유도는 notebooks/probability_loss.ipynb에 있다.
여기서는 PDF, PMF 그림을 그리고, 노트북과 같은 소프트맥스 정의를 다시보내
검증 스크립트가 모듈만으로도 합 조건을 확인하게 한다.
Matplotlib과 Seaborn은 그림에만 사용한다.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

from src.calculus import softmax
from src.plot_style import configure_matplotlib, ensure_parent

configure_matplotlib()


def normal_pdf(x: np.ndarray, mean: float, variance: float) -> np.ndarray:
    """정규분포 N(μ, σ^2)의 확률밀도함수.

    φ(x) = 1 / sqrt(2 π σ^2) * exp( -(x-μ)^2 / (2 σ^2) )

    인자 variance는 분산 σ^2이다. N(2, 0.5)는 평균 2, 분산 0.5이다.
    """
    if variance <= 0.0:
        raise ValueError("분산은 양수여야 한다.")
    values = np.asarray(x, dtype=float)
    scale = np.sqrt(variance)
    coefficient = 1.0 / np.sqrt(2.0 * np.pi * variance)
    return coefficient * np.exp(-0.5 * ((values - mean) / scale) ** 2)


def bernoulli_pmf(probability: float) -> dict[int, float]:
    """베르누이 분포 B(p)의 확률질량함수.

    P(K=1) = p, P(K=0) = 1-p.
    """
    if not 0.0 <= probability <= 1.0:
        raise ValueError("성공 확률은 [0, 1]이어야 한다.")
    return {0: 1.0 - probability, 1: float(probability)}


def plot_normal_pdfs(save_path: str | Path = "outputs/normal_pdf.png") -> None:
    """N(0, 1)과 N(2, 0.5)의 PDF를 한 Figure에 겹쳐 저장한다.

    N(2, 0.5)의 둘째 인자는 분산이다. 표준편차는 sqrt(0.5)이다.
    """
    sns.set_theme(style="whitegrid")
    configure_matplotlib()
    x_coord = np.linspace(-4.0, 6.0, 400)
    figure, axis = plt.subplots(figsize=(7.2, 4.6))
    sns.lineplot(
        x=x_coord,
        y=normal_pdf(x_coord, mean=0.0, variance=1.0),
        ax=axis,
        label=r"$N(0,\ 1)$: $\mu=0,\ \sigma^2=1$",
    )
    sns.lineplot(
        x=x_coord,
        y=normal_pdf(x_coord, mean=2.0, variance=0.5),
        ax=axis,
        label=r"$N(2,\ 0.5)$: $\mu=2,\ \sigma^2=0.5$",
    )
    axis.set_xlabel("x")
    axis.set_ylabel("확률밀도")
    axis.set_title("정규분포 PDF 비교")
    axis.legend()
    figure.tight_layout()
    ensure_parent(save_path)
    figure.savefig(save_path)
    plt.close(figure)


def plot_bernoulli_pmfs(save_path: str | Path = "outputs/bernoulli_pmf.png") -> None:
    """B(0.3)과 B(0.7)의 PMF 막대를 한 Figure에 모아 저장한다."""
    sns.set_theme(style="whitegrid")
    configure_matplotlib()
    distributions = {"B(0.3)": bernoulli_pmf(0.3), "B(0.7)": bernoulli_pmf(0.7)}
    labels: list[str] = []
    outcomes: list[str] = []
    masses: list[float] = []
    for name, table in distributions.items():
        for outcome, mass in table.items():
            labels.append(name)
            outcomes.append(str(outcome))
            masses.append(mass)
    figure, axis = plt.subplots(figsize=(6.6, 4.4))
    sns.barplot(x=outcomes, y=masses, hue=labels, ax=axis)
    axis.set_xlabel("k")
    axis.set_ylabel("P(K=k)")
    axis.set_ylim(0.0, 1.0)
    axis.set_title("베르누이 분포 PMF 비교")
    figure.tight_layout()
    ensure_parent(save_path)
    figure.savefig(save_path)
    plt.close(figure)


def softmax_total_gap(logits: np.ndarray | None = None) -> float:
    """소프트맥스 출력 합과 1의 절대 차이를 반환한다.

    로짓을 생략하면 시드 42의 표준정규 벡터 5개를 쓴다.
    """
    if logits is None:
        generator = np.random.RandomState(42)
        logits = generator.randn(5)
    probabilities = softmax(logits)
    return float(abs(np.sum(probabilities) - 1.0))
