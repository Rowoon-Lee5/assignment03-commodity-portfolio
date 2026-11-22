"""공매도·차입 없는 평균-분산 포트폴리오(원문 각주 5)."""
import numpy as np
import pandas as pd
from scipy.optimize import minimize

합1 = {'type': 'eq', 'fun': lambda w: w.sum() - 1}


def 위험(w, S):
    return float(np.sqrt(w @ S @ w))


def 통계(수익률표):
    if 수익률표.isna().any().any():
        raise ValueError('수익률표에 빈칸이 있음')
    # n으로 나눈다: 원문 표5의 최고 위험이 모표준편차와 같다
    return 수익률표.mean().values, np.cov(수익률표.values, rowvar=False, ddof=0)


def 최소분산(S):
    n = len(S)
    return minimize(lambda w: w @ S @ w, np.full(n, 1 / n), method='SLSQP', bounds=[(0, 1)] * n,
                    constraints=[합1], options={'ftol': 1e-15, 'maxiter': 1000}).x


def 한점(m, S, 목표, 시작):
    """위험 ≤ 목표에서 기대수익이 가장 큰 비중."""
    # SLSQP가 답을 찾고도 실패로 끝날 때가 있어서 조건을 직접 확인
    n, 좋은 = len(m), []
    for x0 in (시작, np.full(n, 1 / n)):
        r = minimize(lambda w: -m @ w, x0, jac=lambda w: -m, method='SLSQP', bounds=[(0, 1)] * n,
                     constraints=[합1, {'type': 'ineq', 'fun': lambda w: 목표 ** 2 - w @ S @ w}],
                     options={'ftol': 1e-10, 'maxiter': 1000})
        w = np.clip(r.x, 0, None) / np.clip(r.x, 0, None).sum()
        if r.x.min() > -1e-8 and abs(r.x.sum() - 1) < 1e-8 and 위험(w, S) <= 목표 + 1e-8:
            좋은.append(w)
        if r.success and 좋은:
            break
    if not 좋은:
        raise RuntimeError(f'위험 {목표}: 조건을 지키는 답을 못 찾음 ({r.message})')
    return max(좋은, key=lambda w: m @ w)


def 프런티어(수익률표, 위험목표):
    """위험목표(월 표준편차 %)마다 비중(%)·기대수익·실제위험. 최소분산보다 낮은 목표는 빈칸."""
    m, S = 통계(수익률표)
    w0 = 최소분산(S)
    줄 = []
    for 목표 in 위험목표:
        if 목표 < 위험(w0, S) - 1e-9:
            줄.append([np.nan] * (len(m) + 2))
            continue
        w = 한점(m, S, 목표, w0)
        줄.append(list(100 * w) + [m @ w, 위험(w, S)])
    열 = list(수익률표.columns) + ['기대수익', '실제위험']
    return pd.DataFrame(줄, index=pd.Index(위험목표, name='위험목표'), columns=열)
