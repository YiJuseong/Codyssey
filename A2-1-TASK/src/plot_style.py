"""시각화 공통 설정.

Matplotlib, Seaborn은 그림 출력에만 사용한다.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager


def configure_matplotlib() -> None:
    """한글 제목이 깨지지 않도록 폰트와 축 스타일을 맞춘다."""
    available = {font.name for font in font_manager.fontManager.ttflist}
    for name in (
        "AppleGothic",
        "Apple SD Gothic Neo",
        "NanumGothic",
        "Noto Sans CJK KR",
        "Malgun Gothic",
    ):
        if name in available:
            plt.rcParams["font.family"] = name
            break
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["figure.dpi"] = 120
    plt.rcParams["savefig.bbox"] = "tight"


def ensure_parent(path: str | Path) -> Path:
    """저장 경로의 상위 디렉터리를 만들고 Path를 반환한다."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    return output
