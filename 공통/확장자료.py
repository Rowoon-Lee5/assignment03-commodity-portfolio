"""확장1 원자재 수단(KRX 금현물, 원자재 선물 ETF, 원자재 민감 업종지수)의 월 수익률. 원문에 없는 우리 추가."""
import json
from datetime import datetime
import pandas as pd
import 자료 as A

폴더 = A.D / 'DataGuide/원자재_업종'
ETF파일 = ('D31_원자재선물ETF8개_종가_수정주가_수정주가TR_거래대금_NAV_달력기준_일간_19900101-20261113.xlsx', 'Sheet1 (2)')
업종파일 = [('D40_코스피업종종가지수18개_건설포함_I31000040F_달력기준_일간_19900101-20261116.xlsx', 'Sheet2'),
           ('sector_tr_dg.xlsx', 'Sheet1')]
# 회원 결정 2026-11-22: ETF는 수정주가, 상장폐지된 TIGER 금속선물(H) 뺀 7개, 업종은 두 논문(이윤정·윤성민 2022, 전지홍 외 2016) 공통인 건설·통신
ETF항목 = '수정주가(원)'
뺄ETF = ['TIGER 금속선물(H)']
업종 = ['코스피 건설', '코스피 통신']


def dg(파일, 시트):
    """DataGuide 엑셀 → 일간 표(열 = (코드명, 아이템명))."""
    x = pd.read_excel(폴더 / 파일, sheet_name=시트, header=None)
    i = next(i for i in range(40) if isinstance(x.iat[i, 0], datetime))
    줄 = {str(x.iat[r, 0]): r for r in range(i)}
    t = x.iloc[i:, 1:].apply(pd.to_numeric, errors='coerce')
    t.index = pd.to_datetime(x.iloc[i:, 0]).rename('날짜')
    t.columns = pd.MultiIndex.from_arrays([x.iloc[줄['코드명'], 1:], x.iloc[줄['아이템명'], 1:]])
    return t


def 거래월말(t):
    """그 달 마지막 거래일 값(빈칸 그대로). 받은 날이 달 중간이라 덜 찬 마지막 달은 뺀다."""
    # 자료.월말()은 빈칸을 건너뛰어 상장폐지 달에 하루치 수익률이 잡히므로 쓰지 않는다.
    m = t.groupby(t.index.to_period('M')).tail(1).iloc[:-1]
    m.index = m.index.to_period('M').to_timestamp('M')
    return m


def krx금():
    """KRX 1kg 금현물(04020000) 종가, 원/g."""
    줄 = [r for f in sorted((A.D / 'KRX/금시장_일별').glob('gold_*.json'))
          for r in json.load(open(f, encoding='utf-8'))['OutBlock_1'] if r['ISU_CD'] == '04020000']
    return A.월말(pd.Series({pd.Timestamp(r['BAS_DD']): float(r['TDD_CLSPRC']) for r in 줄}).sort_index()).rename('KRX금')


def 원자재etf(항목=ETF항목):
    return 거래월말(dg(*ETF파일).xs(항목, axis=1, level=1))


def 업종지수(이름들=업종):
    t = pd.concat([거래월말(dg(f, s).droplevel(1, axis=1)) for f, s in 업종파일], axis=1)
    return t[이름들]


def 확장1수익률(etf항목=ETF항목, etf이름들=None, 업종이름들=업종):
    e = 원자재etf(etf항목)
    e = e.drop(columns=뺄ETF) if etf이름들 is None else e[etf이름들]
    r = A.로그수익률(pd.concat([krx금(), e, 업종지수(업종이름들)], axis=1).asfreq('ME'))
    return r[r.index <= A.끝]


def 기간B(수익률표):
    """모든 열에 값이 있는 첫 달 ~ 마지막 달. 그 안에 빈칸이 있으면 멈춘다."""
    ok = 수익률표.notna().all(axis=1)
    if not ok.any():
        raise ValueError('모든 수단이 함께 있는 달이 없음')
    a, b = ok.idxmax(), 수익률표.index[-1]
    빈 = 수익률표.loc[a:b].isna().any()
    if 빈.any():
        raise ValueError(f'기간 B({a:%Y-%m}~{b:%Y-%m}) 안에 빈칸이 있는 수단: {list(빈[빈].index)}')
    return a, b
