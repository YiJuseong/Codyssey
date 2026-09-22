"""재현 가능한 합성 이커머스 주문 데이터를 생성한다.

각 행은 주문 1건이다. 고객의 최근성·빈도·금액이 고르게 갈리도록 구매 시나리오를 섞었고,
세그먼트 정답 라벨은 저장하지 않는다. 이미지는 카테고리별 밝기 패턴을 가진 16x16 배열이며
CSV ``image_flat`` 컬럼에 공백 구분 소수 문자열로 넣는다.

라이선스: MIT (이 스크립트로 생성한 합성 데이터)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

N_CUSTOMERS = 640
END_DATE = pd.Timestamp("2025-06-30")
FLOOR_DATE = pd.Timestamp("2023-07-01")
OUTLIER_RATE = 0.012
IMAGE_SHAPE = (16, 16)

REGIONS = ["서울", "부산", "인천", "대구", "대전", "광주"]
CHANNELS = ["Web", "App", "Store"]
CHANNEL_P = np.array([0.46, 0.39, 0.15])

BRIGHTNESS = {
    "Electronics": 0.22,
    "Fashion": 0.58,
    "Home": 0.47,
    "Beauty": 0.78,
    "Sports": 0.36,
    "Food": 0.63,
}
RATING_BASE = {
    "Electronics": 4.2,
    "Fashion": 3.9,
    "Home": 4.0,
    "Beauty": 4.5,
    "Sports": 4.1,
    "Food": 3.4,
}

# name, price_low, price_high (원)
RAW_CATALOG: dict[str, list[tuple[str, int, int]]] = {
    "Electronics": [
        ("무선 게이밍 마우스", 32000, 79000),
        ("노이즈캔슬링 블루투스 헤드폰", 89000, 189000),
        ("휴대용 보조배터리 20000mAh", 19000, 45000),
        ("저소음 기계식 키보드", 59000, 129000),
        ("화상회의용 4K 웹캠", 49000, 99000),
        ("스마트워치 교체 밴드 세트", 15000, 39000),
        ("미니 블루투스 스피커", 25000, 69000),
        ("접이식 태블릿 거치대", 12000, 28000),
    ],
    "Fashion": [
        ("오버핏 코튼 후드티", 29000, 69000),
        ("슬림 데님 팬츠", 35000, 79000),
        ("여름 린넨 셔츠", 24000, 52000),
        ("캐시미어 블렌드 머플러", 39000, 89000),
        ("경량 러닝화", 59000, 129000),
        ("데일리 가죽 크로스백", 69000, 149000),
        ("울 블렌드 롱 코트", 129000, 219000),
        ("베이직 양말 5족 세트", 8000, 16000),
    ],
    "Home": [
        ("호텔식 침구 세트 퀸", 69000, 149000),
        ("암막 커튼 2장 세트", 29000, 69000),
        ("스테인리스 프라이팬", 19000, 48000),
        ("향 디퓨저 200ml", 14000, 32000),
        ("LED 스탠드 조명", 22000, 54000),
        ("수납 리빙박스 3개입", 16000, 36000),
        ("주방 칼 3종 세트", 28000, 62000),
        ("극세사 거실 러그", 39000, 89000),
    ],
    "Beauty": [
        ("수분 진정 토너", 12000, 28000),
        ("세라마이드 크림", 18000, 42000),
        ("데일리 선크림 SPF50", 9000, 24000),
        ("저자극 클렌징 폼", 8000, 18000),
        ("헤어 에센스 오일", 14000, 32000),
        ("비타민 세럼", 22000, 48000),
        ("립밤 2개 세트", 6000, 14000),
        ("시트 마스크 10매", 10000, 22000),
    ],
    "Sports": [
        ("요가 매트 10mm", 18000, 42000),
        ("스테인리스 텀블러", 14000, 32000),
        ("홈트 덤벨 세트", 39000, 89000),
        ("러닝 암밴드", 9000, 19000),
        ("방수 스포츠 백팩", 35000, 79000),
        ("폼롤러", 12000, 28000),
        ("등산 스틱 2개입", 29000, 62000),
        ("자전거 헬멧", 39000, 98000),
    ],
    "Food": [
        ("콜드브루 원두 1kg", 18000, 36000),
        ("견과 믹스 500g", 9000, 19000),
        ("그릭요거트 8개입", 7000, 14000),
        ("수제 그래놀라", 8000, 16000),
        ("올리브오일 500ml", 12000, 28000),
        ("허브티 20티백", 6000, 13000),
        ("프로틴 바 12개", 16000, 29000),
        ("제주 감귤 주스 6병", 10000, 18000),
    ],
}

ARCHETYPE_P = {
    "VIP": 0.14,
    "Loyal": 0.26,
    "New": 0.18,
    "AtRisk": 0.18,
    "Churned": 0.24,
}
ARCHETYPE_PARAMS = {
    "VIP": {"n": (10, 22), "last": (0, 18), "gap": (12, 28), "price": (1.20, 1.45), "qty": (1, 3)},
    "Loyal": {"n": (5, 12), "last": (8, 50), "gap": (20, 45), "price": (0.95, 1.20), "qty": (1, 2)},
    "New": {"n": (1, 1), "last": (0, 21), "gap": (30, 60), "price": (0.85, 1.05), "qty": (1, 2)},
    "AtRisk": {"n": (4, 10), "last": (80, 150), "gap": (18, 40), "price": (0.95, 1.25), "qty": (1, 2)},
    "Churned": {"n": (1, 3), "last": (160, 380), "gap": (25, 70), "price": (0.80, 1.10), "qty": (1, 2)},
}
CATEGORY_WEIGHTS = {
    "VIP": {"Electronics": 0.30, "Fashion": 0.22, "Home": 0.12, "Beauty": 0.10, "Sports": 0.18, "Food": 0.08},
    "Loyal": {"Electronics": 0.18, "Fashion": 0.18, "Home": 0.16, "Beauty": 0.16, "Sports": 0.16, "Food": 0.16},
    "New": {"Electronics": 0.08, "Fashion": 0.14, "Home": 0.12, "Beauty": 0.28, "Sports": 0.12, "Food": 0.26},
    "AtRisk": {"Electronics": 0.24, "Fashion": 0.20, "Home": 0.16, "Beauty": 0.12, "Sports": 0.16, "Food": 0.12},
    "Churned": {"Electronics": 0.16, "Fashion": 0.16, "Home": 0.18, "Beauty": 0.18, "Sports": 0.16, "Food": 0.16},
}


def build_catalog() -> list[dict[str, object]]:
    catalog = []
    product_no = 1
    for category, products in RAW_CATALOG.items():
        for name, low, high in products:
            catalog.append(
                {
                    "product_id": f"P{product_no:03d}",
                    "product_name": name,
                    "category": category,
                    "price_low": low,
                    "price_high": high,
                }
            )
            product_no += 1
    return catalog


def order_dates(rng: np.random.Generator, n_orders: int, last_offset: int, gap_low: int, gap_high: int) -> list[pd.Timestamp]:
    last = END_DATE - pd.Timedelta(days=int(last_offset))
    dates = [last]
    cursor = last
    for _ in range(n_orders - 1):
        cursor = cursor - pd.Timedelta(days=int(rng.integers(gap_low, gap_high + 1)))
        if cursor < FLOOR_DATE:
            break
        dates.append(cursor)
    return dates


def choose_product(rng: np.random.Generator, catalog_by_cat: dict[str, list[dict]], archetype: str) -> dict:
    weights = CATEGORY_WEIGHTS[archetype]
    categories = list(weights)
    probabilities = np.array([weights[name] for name in categories], dtype=float)
    probabilities = probabilities / probabilities.sum()
    category = str(rng.choice(categories, p=probabilities))
    pool = catalog_by_cat[category]
    return pool[int(rng.integers(0, len(pool)))]


def format_images(images: np.ndarray) -> list[str]:
    flat = np.round(images.reshape(images.shape[0], -1), 4)
    formatted = np.char.mod("%.4f", flat)
    return [" ".join(row.tolist()) for row in formatted]


def make_images(df: pd.DataFrame, rng: np.random.Generator) -> np.ndarray:
    brightness = df["category"].map(BRIGHTNESS).to_numpy(dtype=float)
    product_no = df["product_id"].str.extract(r"(\d+)", expand=False).astype(int).to_numpy()
    freq = (product_no % 7) + 1
    yy, xx = np.mgrid[0:IMAGE_SHAPE[0], 0:IMAGE_SHAPE[1]]
    base = brightness[:, None, None]
    gradient = (xx / (IMAGE_SHAPE[1] - 1))[None, :, :] * 0.25
    wave = 0.12 * np.sin(xx[None, :, :] * freq[:, None, None] / 4.0)
    noise = rng.normal(0.0, 0.04, size=(len(df),) + IMAGE_SHAPE)
    return np.clip(base + gradient + wave + noise, 0.0, 1.0)


def inject_amount_outliers(df: pd.DataFrame, rng: np.random.Generator) -> None:
    n_out = max(20, int(round(len(df) * OUTLIER_RATE)))
    positions = rng.choice(len(df), size=n_out, replace=False)
    index = df.index.to_numpy()[positions]
    spike = rng.integers(20, 36, size=n_out)
    quantity = df.loc[index, "quantity"].to_numpy() * spike
    unit_price = df.loc[index, "unit_price"].to_numpy()
    quantity = np.maximum(quantity, np.ceil(1_500_000 / unit_price).astype(int))
    df.loc[index, "quantity"] = quantity
    df.loc[index, "amount"] = quantity * unit_price


def generate(rng_orders: np.random.Generator, rng_customers: np.random.Generator) -> pd.DataFrame:
    catalog = build_catalog()
    catalog_by_cat: dict[str, list[dict]] = {}
    for item in catalog:
        catalog_by_cat.setdefault(str(item["category"]), []).append(item)

    names = np.array(list(ARCHETYPE_P))
    probabilities = np.array([ARCHETYPE_P[name] for name in names], dtype=float)
    archetypes = rng_customers.choice(names, size=N_CUSTOMERS, p=probabilities)
    regions = rng_customers.choice(REGIONS, size=N_CUSTOMERS)

    records = []
    order_seq = 1
    for customer_no, archetype in enumerate(archetypes, start=1):
        params = ARCHETYPE_PARAMS[str(archetype)]
        n_orders = int(rng_orders.integers(params["n"][0], params["n"][1] + 1))
        last_offset = int(rng_orders.integers(params["last"][0], params["last"][1] + 1))
        dates = order_dates(rng_orders, n_orders, last_offset, params["gap"][0], params["gap"][1])
        for order_date in dates:
            product = choose_product(rng_orders, catalog_by_cat, str(archetype))
            quantity = int(rng_orders.integers(params["qty"][0], params["qty"][1] + 1))
            base_price = int(rng_orders.integers(int(product["price_low"]), int(product["price_high"]) + 1))
            multiplier = float(rng_orders.uniform(params["price"][0], params["price"][1]))
            unit_price = max(1000, int(round(base_price * multiplier / 100.0) * 100))
            records.append(
                {
                    "order_id": f"O{order_seq:06d}",
                    "customer_id": f"C{customer_no:04d}",
                    "order_date": order_date,
                    "product_id": product["product_id"],
                    "product_name": product["product_name"],
                    "category": product["category"],
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "amount": quantity * unit_price,
                    "region": regions[customer_no - 1],
                    "channel": str(rng_orders.choice(CHANNELS, p=CHANNEL_P)),
                }
            )
            order_seq += 1
    return pd.DataFrame.from_records(records)


def add_ratings(df: pd.DataFrame, rng: np.random.Generator) -> None:
    base = df["category"].map(RATING_BASE).to_numpy(dtype=float)
    rating = np.clip(base + rng.normal(0.0, 0.35, size=len(df)), 1.0, 5.0)
    rating = np.round(rating, 1)
    miss_p = np.where(df["category"].to_numpy() == "Food", 0.22, 0.10)
    rating = rating.astype(float)
    rating[rng.random(len(df)) < miss_p] = np.nan
    df["rating"] = rating


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    out_path = root / "data" / "ecommerce_orders.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    orders = generate(np.random.default_rng(42), np.random.default_rng(7))
    add_ratings(orders, np.random.default_rng(11))
    inject_amount_outliers(orders, np.random.default_rng(13))
    images = make_images(orders, np.random.default_rng(17))
    orders["image_flat"] = format_images(images)
    orders = orders.sort_values(["order_date", "order_id"]).reset_index(drop=True)
    orders.to_csv(out_path, index=False)

    print(f"saved={out_path}")
    print(f"rows={len(orders):,} cols={orders.shape[1]} customers={orders['customer_id'].nunique():,}")
    print(f"date_range={orders['order_date'].min().date()} ~ {orders['order_date'].max().date()}")
    print(f"rating_missing={int(orders['rating'].isna().sum())}")
    print(f"amount_max={int(orders['amount'].max()):,} amount_median={int(orders['amount'].median()):,}")


if __name__ == "__main__":
    main()
