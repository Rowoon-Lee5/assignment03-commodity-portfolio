"""확장2 배분 방식(근거: 박찬·양기성 2022, 60개월 추정·매월 재조정, 위험균형 = 위험기여 균등 p.127). 원문에 없는 우리 추가."""
import numpy as np
import pandas as pd
from scipy.optimize import minimize
import 자료 as A, 최적화 as O


def 동일비중(S):
    return np.full(len(S), 1 / len(S))


def 위험기여(w, S):
    return w * (S @ w) / (w @ S @ w)


def 위험균형(S):
    """위험기여가 모두 같은 비중. z'Rz/2 − Σln z/N 의 최소점에서 z_i(Rz)_i = 1/N 이 된다."""
    # 분산이 100배 넘게 차이 나는 자산(주식·채권)은 S로 풀면 정밀도가 떨어져 상관행렬 R로 푼다.
    sd = np.sqrt(np.diag(S))
    R, n = S / np.outer(sd, sd), len(S)
    r = minimize(lambda z: z @ R @ z / 2 - np.log(z).sum() / n, np.full(n, 1 / np.sqrt(R.sum())),
                 jac=lambda z: R @ z - 1 / (n * z), method='L-BFGS-B', bounds=[(1e-12, None)] * n,
                 options={'ftol': 1e-15, 'gtol': 1e-12, 'maxiter': 10000})
    w = r.x / sd
    w = w / w.sum()
    # L-BFGS-B가 답에 닿고도 ABNORMAL로 끝날 때가 있어(2023-01 등) 성공 표시 대신 위험기여가 같은지 본다.
    if np.abs(위험기여(w, S) - 1 / n).max() > 1e-6:
        raise RuntimeError(f'위험균형 풀이 실패: {r.message}')
    return w


방식들 = {'동일비중': 동일비중, '위험균형': 위험균형, '최소분산': O.최소분산}


def 월별비중(수익률표, 방식, 창=60):
    """t달 비중은 t−창 ~ t−1 달로 정한다. 창 안에 빈칸이 있으면 그 달은 빈칸."""
    f, 줄 = 방식들[방식], {}
    for k in range(창, len(수익률표)):
        과거 = 수익률표.iloc[k - 창:k]
        if not 과거.isna().any().any():
            줄[수익률표.index[k]] = f(O.통계(과거)[1])
    return pd.DataFrame.from_dict(줄, orient='index', columns=수익률표.columns).reindex(수익률표.index)


def 환율분리(원화가격, 원달러=None):
    """원화 가격 → [달러기준, 원달러] 로그수익률(%). 두 열의 합이 원화 수익률(원문 2.2절처럼 환율을 따로 넣기 위함)."""
    fx = A.원달러() if 원달러 is None else 원달러
    p = pd.concat([원화가격 / fx, fx], axis=1, keys=['달러기준', '원달러']).dropna()
    return A.로그수익률(p.asfreq('ME'))
