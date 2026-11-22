"""월 단위 백테스트와 성과 지표. 지표 정의는 과제02 공통/평가.py 성과()와 같다(누적·연환산·연표준편차·샤프·MDD)."""
import numpy as np
import pandas as pd
import 자료 as A

채권열 = ['국고채', '회사채']   # 자료.py에서 채권만 단순수익률, 나머지는 로그수익률


def 단순수익률(수익률표):
    """% → 소수 단순수익률."""
    t = np.exp(수익률표 / 100) - 1
    for c in 채권열:
        if c in t:
            t[c] = 수익률표[c] / 100
    return t


def 무위험():
    """CD 91일 월평균을 월 수익률로 바꿔, t달에는 t−1달 값을 쓴다(그 달 초에 아는 금리)."""
    return (A.채권수익률(A.금리('2010000')) / 100).shift(1).rename('무위험')


def 백테스트(비중표, 수익률표, 비용=0.005):
    """t달 초에 비중표 t줄로 맞추고 t달 수익을 받는다. 비용 = 사고판 비중 합 × 비용(대신증권 AsAP 2025.2의 교체 비용 0.5%)."""
    W = 비중표.dropna()
    if len(pd.date_range(W.index[0], W.index[-1], freq='ME')) != len(W):
        raise ValueError('비중표 중간에 빈 달이 있음')
    R = 단순수익률(수익률표).loc[W.index, W.columns]
    if R.isna().any().any():
        raise ValueError('비중이 있는 달에 수익률 빈칸이 있음')
    흐른 = W * (1 + R)
    회전 = (W - 흐른.div(흐른.sum(axis=1), axis=0).shift(1)).abs().sum(axis=1)
    회전.iloc[0] = np.nan   # 처음 사는 것은 교체가 아니라 비용을 매기지 않는다
    return pd.DataFrame({'수익': (W * R).sum(axis=1) - 비용 * 회전.fillna(0), '회전': 회전})


def 성과(r, rf):
    r = r.dropna()
    ex = r - rf.reindex(r.index)
    w = (1 + r).cumprod()
    return {'첫달': f'{r.index[0]:%Y-%m}', '끝달': f'{r.index[-1]:%Y-%m}', '개월': len(r),
            '누적': w.iloc[-1] - 1, '연환산': w.iloc[-1] ** (12 / len(r)) - 1, '표준편차(연)': r.std() * np.sqrt(12),
            '샤프': ex.mean() / ex.std() * np.sqrt(12), 'MDD': (w / w.cummax().clip(lower=1) - 1).min()}


def 성과표(결과들, rf=None):
    """결과들: {이름: 백테스트() 결과}. 행 = 이름."""
    rf = 무위험() if rf is None else rf
    return pd.DataFrame({k: {**성과(v['수익'], rf), '월평균 회전': v['회전'].mean()} for k, v in 결과들.items()}).T
