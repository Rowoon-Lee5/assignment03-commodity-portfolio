"""원본(../data)을 읽어 월 수익률(%)을 만든다. 자료를 고른 근거는 원문분석/분석_01_김태2008.md."""
import json
from datetime import datetime
from pathlib import Path
import numpy as np
import pandas as pd

D = next(p for p in (Path(__file__).resolve().parents[i] / 'data' for i in (1, 2)) if p.exists())   # 제출본은 공통/ 옆, 작업 폴더는 한 단계 위
캐시 = Path(__file__).resolve().parents[1] / '_캐시'
끝 = '2026-09-30'


def ecos(rel, item2=None):
    r = json.load(open(D / rel, encoding='utf-8'))['StatisticSearch']['row']
    r = [x for x in r if x['DATA_VALUE'] not in (None, '') and (item2 is None or x['ITEM_CODE2'] == item2)]
    t = [x['TIME'] for x in r]
    s = pd.Series([float(x['DATA_VALUE']) for x in r], pd.to_datetime(t, format='%Y%m%d' if len(t[0]) == 8 else '%Y%m'))
    if len(t[0]) == 6:
        s.index = s.index + pd.offsets.MonthEnd(0)
    return s


def 월말(s):
    return s.dropna().resample('ME').last()


def 엑셀열(f, 이름, **kw):
    """DataGuide 엑셀에서 머리글에 '이름'이 있는 열의 일간 값."""
    x = pd.read_excel(f, header=None, **kw)
    i = next(i for i in range(40) if isinstance(x.iat[i, 0], datetime))
    j = next(j for j in range(1, x.shape[1]) if (x.iloc[:i, j].astype(str) == 이름).any())
    return pd.Series(pd.to_numeric(x.iloc[i:, j], errors='coerce').values, pd.to_datetime(x.iloc[i:, 0]))


def kospi():
    return 월말(엑셀열(D / 'DataGuide/주식/X01_지수종가_KOSPI_KOSPITR_K200EW_KOSDAQ_KOSDAQTR_I31000040F_일간_19880101-20260930.xlsx',
                     '코스피', sheet_name='Sheet1 (2)'))


def crb():
    # D33(비영업일 포함): D32는 한국 휴일의 CRB 값이 빠져 월말이 며칠 앞으로 잡힌다.
    f = D / 'DataGuide/원자재_업종/D33_국제상품가격_주요상품가격전체68항목_ECO_달력기준_일간_비영업일포함_19800101-20261113.xlsx'
    c = 캐시 / 'crb_월말_D33.csv'
    if c.exists() and c.stat().st_mtime > f.stat().st_mtime:
        return pd.read_csv(c, index_col=0, parse_dates=True).iloc[:, 0]
    s = 월말(엑셀열(f, '주요상품지수_CRB지수(Futures)(Pt)'))
    캐시.mkdir(exist_ok=True)
    s.rename('CRB').to_csv(c)
    return s


원달러 = lambda: ecos('ECOS/731Y004/731Y004_M_0000001_20261116.json', '0000200')   # 매매기준율 말일자료
ppi부동산 = lambda: ecos('ECOS_Q10조사3/404Y014_M_505AA_20261121.json')
금리 = lambda code: ecos(f'ECOS/721Y001/721Y001_M_{code}_20261116.json')          # 월평균, 연 %


def 로그수익률(p):
    return 100 * np.log(p / p.shift(1))


def 채권수익률(y):
    return 100 * ((1 + y / 100) ** (1 / 12) - 1)



def 월수익률():
    fx = 원달러()
    t = pd.DataFrame({
        '주식': 로그수익률(kospi()),
        '국고채': 채권수익률(금리('5020000')),
        '회사채': 채권수익률(금리('7020000')),
        '부동산_PPI': 로그수익률(ppi부동산()),
        '원자재_CRB원화': 로그수익률(crb() * fx),
        '원자재_CRB달러': 로그수익률(crb()),
        '원달러': 로그수익률(fx),
    })
    return t[t.index <= 끝]


def 스윙켈스(y, 만기=3):
    """월말 금리(연 %) → 채권 월 총수익률(%): 지난달 금리의 이자 − 듀레이션·Δy + ½·볼록성·Δy² (Swinkels 2019 식 1·2, 반년 이자 액면채)."""
    d = y / 100
    z = 1 + d / 2
    D = (1 - z ** (-2 * 만기)) / d
    C = 2 / d ** 2 * (1 - z ** (-2 * 만기)) - 2 * 만기 / (d * z ** (2 * 만기 + 1))
    dy = d.diff()
    return 100 * ((1 + d.shift(1)) ** (1 / 12) - 1 - D * dy + C / 2 * dy ** 2)


def 월수익률_확장():
    """확장2·3용: 채권을 금리 대신 가격 변동이 든 총수익률로 바꾼 판(DataGuide 국고채 총수익지수 FBI.KTB.01.2와 월 수익률 상관 0.99, _검증/설정_시험_20261122.py)."""
    f = D / 'DataGuide/금리/무위험이자율후보_DataGuide_시장금리15종_일간_19880101-20260930.xlsx'
    t = 월수익률()
    t['국고채'] = 스윙켈스(월말(엑셀열(f, '시장금리:국고3년(국채관리기금채3년)(%)')))
    t['회사채'] = 스윙켈스(월말(엑셀열(f, '시장금리:회사채(무보증3년AA-)(%)')))
    return t[t.index <= 끝]

