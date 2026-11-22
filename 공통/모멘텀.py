"""확장3 모멘텀 비중."""
import numpy as np


def 모멘텀(수익률표, 기간):
    """t달 신호 = t−기간 ~ t−1 달 수익률의 합."""
    return 수익률표.rolling(기간, min_periods=기간).sum().shift(1)


def 비중(수익률표, 기간, 무위험, 안전='국고채', 상위=None):
    """무위험보다 더 오른 자산만 갖고 남은 몫은 안전자산에 둔다. 상위=k면 모멘텀 큰 k개만 본다(듀얼)."""
    m = 모멘텀(수익률표.drop(columns=안전).sub(무위험, axis=0), 기간)
    k = m.shape[1] if 상위 is None else 상위
    w = ((m > 0) & (m.rank(axis=1, ascending=False, method='first') <= k)).astype(float) / k
    w[안전] = 1 - w.sum(axis=1)
    w[m.isna().any(axis=1)] = np.nan
    return w[수익률표.columns]
