"""확장3 모멘텀 비중(근거: 대신증권 AsAP 듀얼모멘텀 2025.2, 수업의 한국 모멘텀 3~9개월). 원문에 없는 우리 추가."""
import numpy as np


def 모멘텀(수익률표, 기간):
    """t달 신호 = t−기간 ~ t−1 달 수익률의 합."""
    return 수익률표.rolling(기간, min_periods=기간).sum().shift(1)


def 비중(수익률표, 기간, 무위험, 안전='국고채', 상위=None):
    """후보마다 몫을 나눠 무위험수익률을 넘는 자산만 갖고(절대 모멘텀) 나머지 몫은 안전자산. 상위=k면 모멘텀 큰 k개만 후보(듀얼).
    무위험: 월 %(t달에 t달 동안 받는 값). 절대 모멘텀 기준은 Antonacci(2014)·대신증권 AsAP p.12처럼 무위험 대비 초과수익."""
    m = 모멘텀(수익률표.drop(columns=안전).sub(무위험, axis=0), 기간)
    k = m.shape[1] if 상위 is None else 상위
    w = ((m > 0) & (m.rank(axis=1, ascending=False, method='first') <= k)).astype(float) / k
    w[안전] = 1 - w.sum(axis=1)
    w[m.isna().any(axis=1)] = np.nan
    return w[수익률표.columns]
