"""선형대수: 평면 선형변환, Power Iteration, SVD 이미지 압축.

변환 행렬은 열벡터에 왼쪽에서 곱한다.

    [x']   [a b] [x]
    [y'] = [c d] [y]

면적은 |det(A)|배 된다. 회전 R(θ), 스케일 S(sx, sy), 전단 Sh(k)는
아래 함수가 만드는 2×2 행렬이다.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from src.plot_style import configure_matplotlib, ensure_parent

configure_matplotlib()


def rotation_matrix(theta: float) -> np.ndarray:
    """반시계 방향 회전 행렬 R(θ)를 반환한다.

    R(θ) = [[cos θ, -sin θ],
            [sin θ,  cos θ]]

    det(R) = 1 이므로 넓이는 그대로이고 방향만 바뀐다.
    """
    cosine = np.cos(theta)
    sine = np.sin(theta)
    return np.array([[cosine, -sine], [sine, cosine]], dtype=float)


def scaling_matrix(sx: float, sy: float) -> np.ndarray:
    """축 방향 스케일링 행렬 S(sx, sy)를 반환한다.

    S(sx, sy) = [[sx, 0],
                 [0, sy]]

    det(S) = sx * sy.
    """
    return np.array([[sx, 0.0], [0.0, sy]], dtype=float)


def shear_matrix(k: float) -> np.ndarray:
    """수평 전단 행렬 Sh(k)를 반환한다.

    Sh(k) = [[1, k],
             [0, 1]]

    x' = x + k y, y' = y. det(Sh) = 1.
    """
    return np.array([[1.0, k], [0.0, 1.0]], dtype=float)


def unit_circle(n_points: int = 100) -> np.ndarray:
    """단위 원 위의 점을 순서대로 반환한다.

    theta = linspace(0, 2π, n_points). 반환 shape은 (2, n_points)이고
    첫 행이 x, 둘째 행이 y이다. 닫힌 다각형이 되도록 시작점과 끝점은
    같은 각도 0과 2π이다.
    """
    theta = np.linspace(0.0, 2.0 * np.pi, n_points)
    return np.vstack([np.cos(theta), np.sin(theta)])


def apply_transform(matrix: np.ndarray, points: np.ndarray) -> np.ndarray:
    """2×2 행렬을 (2, N) 점 집합에 적용한다."""
    matrix = np.asarray(matrix, dtype=float)
    points = np.asarray(points, dtype=float)
    if matrix.shape != (2, 2):
        raise ValueError(f"변환 행렬 shape은 (2, 2)여야 한다. 받은 shape: {matrix.shape}") # matrix는 변하는 방식
    if points.shape[0] != 2:
        raise ValueError(f"점 집합 shape은 (2, N)이어야 한다. 받은 shape: {points.shape}") # points는 변하는 주체의 형태
    return matrix @ points


def matrix_determinant(matrix: np.ndarray) -> float:
    """정방행렬의 행렬식 det(A)를 반환한다.

    2×2이면 ad - bc로 직접 계산한다. 더 큰 행렬은 NumPy 행렬식을 사용한다.
    고유값 분해(np.linalg.eig)는 쓰지 않는다.
    """
    matrix = np.asarray(matrix, dtype=float)
    if matrix.shape == (2, 2):
        return float(matrix[0, 0] * matrix[1, 1] - matrix[0, 1] * matrix[1, 0])
    return float(np.linalg.det(matrix))


def polygon_area(points: np.ndarray) -> float:
    """꼭짓점 순서 (2, N)에 신발끈 공식으로 다각형 면적을 구한다.

    Area = 1/2 |Σ (x_i y_{i+1} - x_{i+1} y_i)|
    """
    points = np.asarray(points, dtype=float)
    x_coord = points[0]
    y_coord = points[1]
    return 0.5 * abs(
        float(np.dot(x_coord, np.roll(y_coord, -1)) - np.dot(y_coord, np.roll(x_coord, -1)))
    )


def area_ratio_vs_determinant(matrix: np.ndarray, points: np.ndarray) -> dict[str, float]:
    """|det(A)|와 변환 전후 면적비를 비교한다.

    선형변환은 도형의 면적을 |det(A)|배 한다. 상대오차는
    ||det(A)| - area_ratio| / |det(A)| 이다. det이 0이면 절대오차를 쓴다.

    Returns:
        determinant, abs_determinant, area_before, area_after, area_ratio, relative_error.
    """
    transformed = apply_transform(matrix, points)
    area_before = polygon_area(points)
    area_after = polygon_area(transformed)
    if area_before == 0.0:
        raise ValueError("변환 전 면적이 0이다.")
    determinant = matrix_determinant(matrix)
    abs_determinant = abs(determinant)
    area_ratio = area_after / area_before
    if abs_determinant == 0.0:
        relative_error = abs(area_ratio - abs_determinant)
    else:
        relative_error = abs(area_ratio - abs_determinant) / abs_determinant
    return {
        "determinant": determinant,
        "abs_determinant": abs_determinant,
        "area_before": area_before,
        "area_after": area_after,
        "area_ratio": area_ratio,
        "relative_error": relative_error,
    }


def plot_linear_transform(
    matrix: np.ndarray,
    title: str,
    save_path: str | Path,
    points: np.ndarray | None = None,
) -> dict[str, float]:
    """단위 원과 선형변환 결과를 한 Figure에 겹쳐 저장한다.

    변환 전은 파란 실선, 변환 후는 주황 실선이다. 그림 안에 det(A)와
    면적비의 상대오차를 적는다.
    """
    if points is None:
        points = unit_circle(100)
    transformed = apply_transform(matrix, points)
    stats = area_ratio_vs_determinant(matrix, points)

    figure, axis = plt.subplots(figsize=(6.2, 6.2))
    axis.plot(points[0], points[1], color="#1f77b4", linewidth=2.0, label="변환 전 (단위 원)")
    axis.plot(
        transformed[0],
        transformed[1],
        color="#ff7f0e",
        linewidth=2.0,
        label="변환 후",
    )
    axis.axhline(0.0, color="0.6", linewidth=0.6)
    axis.axvline(0.0, color="0.6", linewidth=0.6)
    axis.set_aspect("equal", adjustable="box")
    axis.set_xlabel("x")
    axis.set_ylabel("y")
    axis.set_title(title)
    axis.legend(loc="upper right")
    axis.text(
        0.02,
        0.02,
        (
            f"det(A) = {stats['determinant']:.4f}\n"
            f"면적비 = {stats['area_ratio']:.4f}\n"
            f"상대오차 = {stats['relative_error']:.2e}"
        ),
        transform=axis.transAxes,
        va="bottom",
        ha="left",
        fontsize=9,
        bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.9},
    )
    figure.tight_layout()
    ensure_parent(save_path)
    figure.savefig(save_path)
    plt.close(figure)
    return stats


def plot_rotation(theta: float, save_path: str | Path) -> dict[str, float]:
    """단위 원에 R(θ)를 적용하고 변환 전후를 한 Figure에 저장한다."""
    degrees = np.degrees(theta)
    return plot_linear_transform(
        rotation_matrix(theta),
        title=fr"회전 $R(\theta)$, $\theta={degrees:.0f}^\circ$",
        save_path=save_path,
    )


def plot_scaling(sx: float, sy: float, save_path: str | Path) -> dict[str, float]:
    """단위 원에 S(sx, sy)를 적용하고 타원 결과를 저장한다."""
    return plot_linear_transform(
        scaling_matrix(sx, sy),
        title=fr"스케일링 $S({sx:g},\ {sy:g})$",
        save_path=save_path,
    )


def plot_shear(k: float, save_path: str | Path) -> dict[str, float]:
    """단위 원에 Sh(k)를 적용하고 기울어진 결과를 저장한다."""
    return plot_linear_transform(
        shear_matrix(k),
        title=fr"전단 $Sh(k)$, $k={k:g}$",
        save_path=save_path,
    )


def power_iteration(
    matrix: np.ndarray,
    n_iter: int = 500,
    tol: float = 1e-12,
    initial_vector: np.ndarray | None = None,
) -> tuple[float, np.ndarray]:
    """Power Iteration으로 절대값이 가장 큰 고유값과 고유벡터를 구한다.

    반복식:

        w_{k+1} = A v_k
        v_{k+1} = w_{k+1} / ||w_{k+1}||
        λ_{k+1} = v_{k+1}^T A v_{k+1}

    Rayleigh 몫 λ는 대칭행렬에서 지배 고유값으로 수렴한다.
    이 함수는 np.linalg.eig를 호출하지 않는다. 비교 검증은
    reference_dominant_eigenvalue()에서만 한다.

    초기 벡터를 생략하면 RandomState(42)로 만든다. 전역 시드는 바꾸지 않는다.

    Returns:
        eigenvalue: 스칼라 λ.
        eigenvector: L2 노름이 1인 shape (n,) 벡터.
    """
    matrix = np.asarray(matrix, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError(f"정방행렬이 필요하다. 받은 shape: {matrix.shape}")
    if initial_vector is None:
        generator = np.random.RandomState(42)
        vector = generator.randn(matrix.shape[0])
    else:
        vector = np.asarray(initial_vector, dtype=float).reshape(-1)
        if vector.shape[0] != matrix.shape[0]:
            raise ValueError("초기 벡터 길이가 행렬 크기와 다르다.")
    norm = np.linalg.norm(vector)
    if norm == 0.0:
        raise ValueError("초기 벡터의 노름이 0이다.")
    vector = vector / norm
    eigenvalue = 0.0
    for _ in range(n_iter):
        transformed = matrix @ vector
        transformed_norm = np.linalg.norm(transformed)
        if transformed_norm == 0.0:
            return 0.0, vector
        next_vector = transformed / transformed_norm
        eigenvalue = float(next_vector @ (matrix @ next_vector))
        aligned = next_vector if np.dot(next_vector, vector) >= 0.0 else -next_vector
        if np.linalg.norm(aligned - vector) < tol:
            vector = aligned
            break
        vector = next_vector
    return eigenvalue, vector


def reference_dominant_eigenvalue(matrix: np.ndarray) -> float:
    """검증 전용: np.linalg.eig로 절대값 최대 고유값을 구한다.

    Power Iteration 구현의 오차를 확인할 때만 호출한다.
    고유값을 구하는 알고리즘 자체는 power_iteration()이다.
    """
    eigenvalues = np.linalg.eig(np.asarray(matrix, dtype=float))[0]
    index = int(np.argmax(np.abs(eigenvalues)))
    return float(np.real(eigenvalues[index]))


def symmetric_demo_matrix(n: int = 5) -> np.ndarray:
    """시드 42의 대칭행렬을 만든다.

    M = (G + G^T) / 2, G의 원소는 표준정규분포이다.
    대칭이므로 고유값은 실수이고 Power Iteration의 Rayleigh 몫이
    지배 고유값으로 수렴한다.
    """
    generator = np.random.RandomState(42)
    raw = generator.randn(n, n)
    return (raw + raw.T) / 2.0


def make_grayscale_image(size: int = 64) -> np.ndarray:
    """SVD 압축 실험용 64×64 이하 회색조 이미지를 만든다.

    저주파 기울기, 원, 대각 띠, 모서리의 바둑판을 섞어
    k에 따라 복원 차이가 보이게 했다. 값의 범위는 [0, 1]이다.
    공개 사진을 받지 않고, 같은 코드로 항상 같은 배열이 나온다.
    """
    if size > 64:
        raise ValueError("과제 조건에 맞춰 한 변은 64 이하여야 한다.")
    ys, xs = np.mgrid[0:size, 0:size]
    x_coord = xs / (size - 1)
    y_coord = ys / (size - 1)
    image = 0.15 + 0.25 * x_coord + 0.15 * y_coord
    image = image + 0.20 * np.sin(2.0 * np.pi * 3.0 * x_coord) * np.cos(
        2.0 * np.pi * 2.0 * y_coord
    )
    circle = (x_coord - 0.35) ** 2 + (y_coord - 0.40) ** 2 <= 0.12 ** 2
    image = np.where(circle, 0.95, image)
    band = np.abs(y_coord - x_coord) < 0.035
    image = np.where(band, 0.08, image)
    checker = ((np.floor(xs / 2.0) + np.floor(ys / 2.0)) % 2).astype(float)
    corner = (x_coord > 0.72) & (y_coord > 0.72)
    image = np.where(corner, 0.15 + 0.75 * checker, image)
    return np.clip(image, 0.0, 1.0)


def svd_reconstruct(image: np.ndarray, k: int) -> np.ndarray:
    """SVD 상위 k개 성분으로 이미지를 복원한다.

    A = U diag(s) Vh 일 때

        A_k = U[:, :r] diag(s[:r]) Vh[:r, :]
        r = min(k, m, n)

    k가 랭크 상한보다 크면 전체 복원과 같다. 64×64 이미지에서
    k=100은 r=64로 잘린다. np.linalg.svd를 쓰고, PCA 구현 라이브러리는
    쓰지 않는다.
    """
    image = np.asarray(image, dtype=float)
    if image.ndim != 2:
        raise ValueError(f"회색조 2차원 이미지가 필요하다. 받은 ndim: {image.ndim}")
    if k < 1:
        raise ValueError("k는 1 이상이어야 한다.")
    left, singular, right = np.linalg.svd(image, full_matrices=False)
    rank = min(k, singular.shape[0])
    reconstructed = (left[:, :rank] * singular[:rank]) @ right[:rank, :]
    return reconstructed


def relative_frobenius_error(original: np.ndarray, reconstructed: np.ndarray) -> float:
    """||A - A_k||_F / ||A||_F 를 반환한다."""
    denominator = np.linalg.norm(original)
    if denominator == 0.0:
        raise ValueError("원본 이미지의 노름이 0이다.")
    return float(np.linalg.norm(original - reconstructed) / denominator)


def plot_svd_compression(
    image: np.ndarray,
    ks: tuple[int, ...] = (10, 50, 100),
    save_path: str | Path = "outputs/svd_compression.png",
) -> dict[int, float]:
    """원본과 k=10, 50, 100 복원을 한 Figure에 나란히 저장한다.

    Returns:
        각 k의 상대 Frobenius 오차. k가 랭크보다 크면 실제 사용 랭크는 잘린다.
    """
    image = np.asarray(image, dtype=float)
    errors: dict[int, float] = {}
    figure, axes = plt.subplots(1, len(ks) + 1, figsize=(3.3 * (len(ks) + 1), 3.6))
    panels = [("원본", image)]
    max_rank = min(image.shape)
    for k in ks:
        restored = svd_reconstruct(image, k)
        used = min(k, max_rank)
        errors[k] = relative_frobenius_error(image, restored)
        label = f"k={k}" if used == k else f"k={k} (r={used})"
        panels.append((label, np.clip(restored, 0.0, 1.0)))
    for axis, (label, panel) in zip(axes, panels):
        axis.imshow(panel, cmap="gray", vmin=0.0, vmax=1.0)
        suffix = ""
        if label.startswith("k="):
            k_value = int(label.split()[0].split("=")[1])
            suffix = f"\n상대오차 {errors[k_value]:.2e}"
        axis.set_title(label + suffix)
        axis.axis("off")
    figure.suptitle("SVD 이미지 압축과 복원", y=1.02)
    figure.tight_layout()
    ensure_parent(save_path)
    figure.savefig(save_path)
    plt.close(figure)
    return errors
