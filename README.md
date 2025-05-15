# 네이버 애널리틱스 대시보드

네이버 애널리틱스 데이터를 시각화하고 분석하는 대시보드입니다.

## 기능

- 일별 방문자수 추이 시각화
- 광고 효과 분석
- 요일별 방문자수 분석
- 주말/평일 구분 표시

## 설치 방법

1. 필요한 패키지 설치:
```bash
pip install streamlit pandas plotly matplotlib statsmodels
```

2. 데이터 파일 준비:
- `data/` 디렉토리에 필요한 데이터 파일들을 위치시킵니다.
- 광고 데이터는 `data/ads/` 디렉토리에 위치시킵니다.

## 실행 방법

```bash
streamlit run na_ads_dashboard.py
```

## 데이터 구조

- 방문자수 데이터: `data/uv_data.xlsx`
- 광고 데이터: `data/ads/ad_2025_02_2025_05.csv`
- 기타 분석 데이터: `data/*_data.xlsx` 