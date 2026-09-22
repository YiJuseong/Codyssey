"""멀티모달 이커머스 데이터를 처리하는 객체 지향 분석 파이프라인.

수치, 텍스트, 이미지 배열을 한 테이블에서 다루고 결측치 대치, IQR 이상치 탐지,
RFM 고객 세분화를 수행한다. 이미지 특징은 행 단위 반복문 없이 NumPy 배열 연산으로 계산한다.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


SEGMENT_ORDER = ["VIP", "Loyal", "New", "At Risk", "Churned", "Regular"]
IMAGE_SOURCE_SHAPE = (16, 16)
IMAGE_DOWNSAMPLE_STEP = 2


def iqr_bounds(series: pd.Series, threshold: float = 1.5) -> dict[str, float]:
    """IQR 울타리를 계산한다.

    하한은 Q1 - threshold * IQR, 상한은 Q3 + threshold * IQR 이다.
    """
    q1 = float(series.quantile(0.25))
    q3 = float(series.quantile(0.75))
    iqr = q3 - q1
    return {
        "q1": q1,
        "q3": q3,
        "iqr": iqr,
        "lower": q1 - threshold * iqr,
        "upper": q3 + threshold * iqr,
        "threshold": float(threshold),
    }


def score_by_quantile(series: pd.Series, higher_is_better: bool, bins: int = 5) -> pd.Series:
    """값을 분위 점수(1~bins)로 변환한다. 동점은 rank로 깨서 qcut 경계 오류를 피한다."""
    ranked = series.rank(method="first", ascending=higher_is_better)
    labels = list(range(1, bins + 1))
    return pd.qcut(ranked, bins, labels=labels).astype(int)


def assign_rfm_segment(r_score: np.ndarray, f_score: np.ndarray, m_score: np.ndarray) -> np.ndarray:
    """R, F, M 점수(1~5)로 고객 세그먼트를 부여한다. 먼저 일치한 규칙이 우선한다."""
    r = np.asarray(r_score)
    f = np.asarray(f_score)
    m = np.asarray(m_score)
    segment = np.full(r.shape, "Regular", dtype=object)
    rules = [
        ((r >= 4) & (f >= 4) & (m >= 4), "VIP"),
        ((r >= 3) & (f >= 3) & (m >= 3), "Loyal"),
        ((r >= 4) & (f <= 2), "New"),
        ((r <= 2) & (f >= 3) & (m >= 3), "At Risk"),
        ((r <= 2) & (f <= 2), "Churned"),
    ]
    for condition, name in rules:
        # 이미 더 구체적인 세그먼트가 있으면 덮어쓰지 않는다.
        segment = np.where(condition & (segment == "Regular"), name, segment)
    return segment


class DataAnalyzer:
    """원본 주문을 전처리하고 피처와 요약 통계, RFM 세그먼트를 만든다."""

    def __init__(self, data_path: str | Path):
        self.data_path = Path(data_path)
        self.df: pd.DataFrame | None = None
        self.rfm: pd.DataFrame | None = None
        self.reference_date: pd.Timestamp | None = None
        self.outlier_bounds: dict[str, dict[str, float]] = {}

    def load_data(self, date_col: str = "order_date") -> pd.DataFrame:
        """CSV를 읽고 날짜 컬럼을 datetime으로 변환한다."""
        self.df = pd.read_csv(self.data_path)
        if date_col in self.df.columns:
            self.df[date_col] = pd.to_datetime(self.df[date_col])
        return self.df

    def restore_images(self, flat_col: str = "image_flat", shape: tuple[int, int] = IMAGE_SOURCE_SHAPE) -> np.ndarray:
        """CSV에 공백으로 저장된 이미지 문자열을 NumPy 배열로 복구한다.

        행마다 ``fromstring``을 반복하지 않고, 열 전체를 이어 붙인 뒤 한 번에 변환한다.
        """
        self._require_df()
        if flat_col not in self.df.columns:
            raise KeyError(f"이미지 컬럼이 없습니다: {flat_col}")
        flat_text = " ".join(self.df[flat_col].astype(str).str.strip().tolist())
        values = np.fromstring(flat_text, sep=" ")
        expected = len(self.df) * int(np.prod(shape))
        if values.size != expected:
            raise ValueError(
                f"이미지 원소 수가 맞지 않습니다. 기대값 {expected}, 실제값 {values.size}. "
                f"shape={shape}"
            )
        return values.reshape((len(self.df),) + tuple(shape))

    def add_image_features(
        self,
        flat_col: str = "image_flat",
        source_shape: tuple[int, int] = IMAGE_SOURCE_SHAPE,
        downsample_step: int = IMAGE_DOWNSAMPLE_STEP,
    ) -> pd.DataFrame:
        """이미지 평균과 표준편차를 배열 연산으로 계산해 컬럼에 추가한다.

        ``downsample_step``이 1보다 크면 ``arr[:, ::step, ::step]`` 슬라이싱으로
        다운샘플한 뒤 특징을 구한다.
        """
        images = self.restore_images(flat_col=flat_col, shape=source_shape)
        if downsample_step > 1:
            images = images[:, ::downsample_step, ::downsample_step]
        # (n, h, w) 배치 전체에 대해 공간 축만 축소한다. 파이썬 for 루프를 쓰지 않는다.
        self.df["image_mean"] = images.mean(axis=(1, 2))
        self.df["image_std"] = images.std(axis=(1, 2))
        return self.df

    def add_text_features(self, text_col: str = "product_name") -> pd.DataFrame:
        """상품명 문자열 길이와 공백 기준 단어 수를 파생 변수로 추가한다."""
        self._require_df()
        if text_col not in self.df.columns:
            raise KeyError(f"텍스트 컬럼이 없습니다: {text_col}")
        names = self.df[text_col].fillna("").astype(str)
        self.df["name_length"] = names.str.len()
        self.df["name_word_count"] = names.str.split().str.len()
        return self.df

    def missing_summary(self) -> pd.DataFrame:
        """컬럼별 결측 건수와 비율을 반환한다."""
        self._require_df()
        count = self.df.isna().sum()
        summary = pd.DataFrame({"missing_count": count, "missing_rate": count / len(self.df)})
        return summary.sort_values("missing_count", ascending=False)

    def handle_missing_values(
        self,
        strategy: str = "group_mean",
        group_col: str | None = None,
        target_col: str | None = None,
    ) -> dict[str, object]:
        """결측치를 대치한다.

        ``group_mean`` / ``group_median``은 그룹 통계로 채운 뒤, 그룹 전체가 결측이면
        전체 평균 또는 중앙값으로 한 번 더 채운다.
        """
        self._require_df()
        if target_col is None:
            raise ValueError("target_col은 필수입니다.")
        if target_col not in self.df.columns:
            raise KeyError(f"대상 컬럼이 없습니다: {target_col}")

        missing_before = int(self.df[target_col].isna().sum())
        if strategy == "group_mean":
            self._fill_with_group(target_col, group_col, "mean")
        elif strategy == "group_median":
            self._fill_with_group(target_col, group_col, "median")
        elif strategy == "mean":
            self.df[target_col] = self.df[target_col].fillna(self.df[target_col].mean())
        elif strategy == "median":
            self.df[target_col] = self.df[target_col].fillna(self.df[target_col].median())
        else:
            raise ValueError(f"지원하지 않는 대치 전략입니다: {strategy}")

        missing_after = int(self.df[target_col].isna().sum())
        return {
            "column": target_col,
            "strategy": strategy,
            "group_col": group_col,
            "missing_before": missing_before,
            "missing_after": missing_after,
        }

    def detect_outliers(self, column: str, threshold: float = 1.5) -> pd.DataFrame:
        """IQR 방식으로 이상치 행을 반환한다. 원본 데이터는 바꾸지 않는다."""
        self._require_df()
        if column not in self.df.columns:
            raise KeyError(f"컬럼이 없습니다: {column}")
        bounds = iqr_bounds(self.df[column], threshold=threshold)
        self.outlier_bounds[column] = bounds
        mask = (self.df[column] < bounds["lower"]) | (self.df[column] > bounds["upper"])
        return self.df.loc[mask].copy()

    def treat_outliers(self, column: str, threshold: float = 1.5, method: str = "clip") -> dict[str, object]:
        """이상치를 울타리 값으로 캡핑하거나 해당 행을 제거한다.

        주문 금액을 통째로 지우면 구매 빈도까지 줄어들므로 기본값은 캡핑이다.
        """
        outliers = self.detect_outliers(column, threshold=threshold)
        bounds = self.outlier_bounds[column]
        if method == "clip":
            self.df[column] = self.df[column].clip(lower=bounds["lower"], upper=bounds["upper"])
        elif method == "remove":
            self.df = self.df.loc[~self.df.index.isin(outliers.index)].copy()
        else:
            raise ValueError(f"지원하지 않는 이상치 처리 방법입니다: {method}")
        return {"column": column, "n_outliers": int(len(outliers)), "method": method, "bounds": bounds}

    def recalculate_amount(
        self,
        price_col: str = "unit_price",
        qty_col: str = "quantity",
        amount_col: str = "amount",
    ) -> pd.DataFrame:
        """수량과 단가로 주문 금액을 다시 계산한다.

        수량 이상치를 울타리로 캡핑한 뒤에도 ``amount``가 ``quantity * unit_price``와
        같게 유지한다. 주문 행 자체는 지우지 않아 구매 빈도가 줄지 않는다.
        """
        self._require_df()
        for column in (price_col, qty_col):
            if column not in self.df.columns:
                raise KeyError(f"컬럼이 없습니다: {column}")
        self.df[amount_col] = self.df[qty_col] * self.df[price_col]
        return self.df

    def summary_statistics(self, columns: list[str]) -> pd.DataFrame:
        """지정한 수치형 변수의 평균, 중앙값, 표준편차, 사분위수를 계산한다."""
        self._require_df()
        rows = []
        for column in columns:
            series = self.df[column].dropna()
            rows.append(
                {
                    "column": column,
                    "count": int(series.count()),
                    "mean": float(series.mean()),
                    "median": float(series.median()),
                    "std": float(series.std()),
                    "min": float(series.min()),
                    "q1": float(series.quantile(0.25)),
                    "q2": float(series.quantile(0.50)),
                    "q3": float(series.quantile(0.75)),
                    "max": float(series.max()),
                }
            )
        return pd.DataFrame(rows)

    def correlation_matrix(self, columns: list[str], method: str = "pearson") -> pd.DataFrame:
        """수치형 변수들의 상관계수 행렬을 반환한다."""
        self._require_df()
        return self.df[columns].corr(method=method)

    def calculate_rfm(
        self,
        customer_col: str = "customer_id",
        date_col: str = "order_date",
        amount_col: str = "amount",
        reference_date: str | pd.Timestamp | None = None,
        score_bins: int = 5,
    ) -> pd.DataFrame:
        """고객별 Recency, Frequency, Monetary와 세그먼트를 계산한다.

        기준일을 생략하면 데이터의 최종 거래일을 기준일로 쓴다.
        Recency는 기준일에서 마지막 구매일까지 지난 일수이며, 작을수록 점수가 높다.
        """
        self._require_df()
        for column in (customer_col, date_col, amount_col):
            if column not in self.df.columns:
                raise KeyError(f"RFM 계산에 필요한 컬럼이 없습니다: {column}")

        work = self.df.dropna(subset=[customer_col, date_col, amount_col]).copy()
        if not np.issubdtype(work[date_col].dtype, np.datetime64):
            work[date_col] = pd.to_datetime(work[date_col])

        if reference_date is None:
            resolved_date = pd.Timestamp(work[date_col].max())
        else:
            resolved_date = pd.Timestamp(reference_date)
        self.reference_date = resolved_date

        rfm = work.groupby(customer_col, as_index=True).agg(
            last_purchase=(date_col, "max"),
            first_purchase=(date_col, "min"),
            frequency=(date_col, "count"),
            monetary=(amount_col, "sum"),
        )
        rfm["recency"] = (resolved_date - rfm["last_purchase"]).dt.days.astype(int)
        rfm["avg_order_value"] = rfm["monetary"] / rfm["frequency"]
        rfm["R_score"] = score_by_quantile(rfm["recency"], higher_is_better=False, bins=score_bins)
        rfm["F_score"] = score_by_quantile(rfm["frequency"], higher_is_better=True, bins=score_bins)
        rfm["M_score"] = score_by_quantile(rfm["monetary"], higher_is_better=True, bins=score_bins)
        rfm["RFM_score"] = rfm["R_score"] + rfm["F_score"] + rfm["M_score"]
        rfm["segment"] = assign_rfm_segment(
            rfm["R_score"].to_numpy(),
            rfm["F_score"].to_numpy(),
            rfm["M_score"].to_numpy(),
        )
        self.rfm = rfm
        return rfm

    def segment_profile(self) -> pd.DataFrame:
        """세그먼트별 고객 수, 평균 RFM, 매출 기여도를 요약한다."""
        if self.rfm is None:
            raise RuntimeError("calculate_rfm()을 먼저 호출해야 합니다.")
        profile = self.rfm.groupby("segment", as_index=True).agg(
            customers=("recency", "size"),
            avg_recency=("recency", "mean"),
            median_recency=("recency", "median"),
            avg_frequency=("frequency", "mean"),
            avg_monetary=("monetary", "mean"),
            median_monetary=("monetary", "median"),
            avg_order_value=("avg_order_value", "mean"),
            total_monetary=("monetary", "sum"),
        )
        profile["customer_share"] = profile["customers"] / profile["customers"].sum()
        profile["revenue_share"] = profile["total_monetary"] / profile["total_monetary"].sum()
        ordered = [name for name in SEGMENT_ORDER if name in profile.index]
        extra = [name for name in profile.index if name not in ordered]
        return profile.loc[ordered + extra]

    def _fill_with_group(self, target_col: str, group_col: str | None, stat: str) -> None:
        if group_col is None:
            raise ValueError(f"{stat} 그룹 대치에는 group_col이 필요합니다.")
        if group_col not in self.df.columns:
            raise KeyError(f"그룹 컬럼이 없습니다: {group_col}")
        grouped = self.df.groupby(group_col)[target_col].transform(stat)
        self.df[target_col] = self.df[target_col].fillna(grouped)
        fallback = getattr(self.df[target_col], stat)()
        self.df[target_col] = self.df[target_col].fillna(fallback)

    def _require_df(self) -> None:
        if self.df is None:
            raise RuntimeError("load_data()를 먼저 호출해야 합니다.")


def default_data_path() -> Path:
    return Path(__file__).resolve().parents[1] / "data" / "ecommerce_orders.csv"


def run_demo(data_path: str | Path | None = None) -> None:
    """전처리부터 RFM 요약까지 한 번 실행하고 핵심 수치를 출력한다."""
    analyzer = DataAnalyzer(data_path or default_data_path())
    frame = analyzer.load_data()
    print(f"rows={len(frame):,} cols={frame.shape[1]}")
    print(f"date_range={frame['order_date'].min().date()} ~ {frame['order_date'].max().date()}")
    analyzer.add_image_features()
    analyzer.add_text_features()
    missing = analyzer.handle_missing_values(strategy="group_mean", group_col="category", target_col="rating")
    print(
        "rating imputation:",
        f"{missing['missing_before']} -> {missing['missing_after']}",
        f"strategy={missing['strategy']} group={missing['group_col']}",
    )
    amount_outliers = analyzer.detect_outliers("amount", threshold=1.5)
    amount_bounds = analyzer.outlier_bounds["amount"]
    print(
        f"amount iqr outliers={len(amount_outliers)} "
        f"lower={amount_bounds['lower']:.0f} upper={amount_bounds['upper']:.0f}"
    )
    treated = analyzer.treat_outliers("quantity", threshold=1.5, method="clip")
    analyzer.recalculate_amount()
    bounds = treated["bounds"]
    print(
        f"quantity outliers={treated['n_outliers']} "
        f"lower={bounds['lower']:.2f} upper={bounds['upper']:.2f} "
        f"amount_max_after={analyzer.df['amount'].max():.0f}"
    )
    analyzer.calculate_rfm()
    print(f"rfm_reference_date={analyzer.reference_date.date()} customers={len(analyzer.rfm):,}")
    profile = analyzer.segment_profile()
    display_cols = ["customers", "customer_share", "avg_recency", "avg_frequency", "avg_monetary", "revenue_share"]
    print(profile[display_cols].round(2).to_string())


if __name__ == "__main__":
    run_demo()
