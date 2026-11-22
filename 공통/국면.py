"""국면 이름표(원문 p.22, 규칙은 Jensen·Johnson·Mercer 2000)와 국면을 나눌 금리 후보. 근거: _검증/Q5_재할인율_조사_20261116.md"""
import pandas as pd
import 자료 as A


def 이름표(s, start, end):
    """달마다 '확장'(최근 변화가 하락)·'긴축'(상승)·'혼합'(방향이 바뀐 달)·'모름'(앞선 변화 없음)."""
    d = s.diff().dropna()
    d = d[d != 0]
    sg = (d > 0).astype(int) * 2 - 1
    new = sg != sg.shift(1)
    new.iloc[0] = False   # 자료의 첫 변화는 앞 방향을 모르므로 방향 전환으로 보지 않음
    m = sg.index.to_period('M')
    out = {}
    for p in pd.period_range(start, end, freq='M'):
        if new[m == p].any():
            out[p] = '혼합'
            continue
        past = sg[m <= p]
        out[p] = '모름' if len(past) == 0 else ('확장' if past.iloc[-1] < 0 else '긴축')
    return pd.Series(out)


def fred(rel):
    x = pd.read_csv(A.D / rel)
    x = x[x.iloc[:, 1].astype(str) != '.']
    return pd.Series(x.iloc[:, 1].astype(float).values, pd.to_datetime(x.iloc[:, 0]))


def 잇기(앞, 뒤, 끝='1999-04-30'):
    """끝까지는 앞 금리, 그 뒤는 뒤 금리. 이은 곳의 값 차이는 변화로 세지 않는다."""
    a, b = 앞[앞.index <= 끝], 뒤[뒤.index > 끝]
    return pd.concat([a, b - b.iloc[0] + a.iloc[-1]])


후보 = {
    '총액한도대출금리(일간)': lambda: A.ecos('ECOS/722Y001/722Y001_D_0109000_20261116.json'),
    '총액한도대출금리(월간)': lambda: A.ecos('ECOS/722Y001/722Y001_M_0109000_20261116.json'),
    'IMF 한국 재할인율(월간)': lambda: fred('FRED/INTDSRKRM193N_20261116.csv'),
    '기준금리(일간, 1999-05~)': lambda: A.ecos('ECOS/722Y001/722Y001_D_0101000_20261116.json'),
    '정부대출금금리(일간)': lambda: A.ecos('ECOS/722Y001/722Y001_D_0102000_20261116.json'),
    '콜금리 1일(일간)': lambda: A.ecos('ECOS/817Y002/817Y002_D_010101000_20261116.json'),
    '무담보콜금리 1일(월간)': lambda: A.금리('1010000'),
    'CD 91일(월간)': lambda: A.금리('2010000'),
    '통안증권 1년(월간)': lambda: A.금리('6010100'),
}
# 회원 결정 2026-11-22: 본 결과는 재할인율(~1999-04) + 기준금리(1999-05~, 발표 시작 달), 보조는 CD 91일
후보['재할인율→기준금리'] = lambda: 잇기(후보['IMF 한국 재할인율(월간)'](), 후보['기준금리(일간, 1999-05~)']())
본국면, 보조국면 = '재할인율→기준금리', 'CD 91일(월간)'
