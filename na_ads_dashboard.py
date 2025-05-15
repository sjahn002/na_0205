import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import timedelta
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib import font_manager, rc

# 페이지 설정
st.set_page_config(
    
    page_title="네이버 애널리틱스 대시보드",
    page_icon="📊",
    layout="wide"
)

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 데이터 로드 함수
@st.cache_data
def load_data():
    # 데이터프레임 파일 목록 정의
    df_files = [
        'browserDashboard', 'durationTime', 'endPage', 'osDashboard',
        'popularPage', 'pv', 'resolutionDashboard', 'returnPage',
        'startPage', 'timeline', 'urls', 'uv'
    ]

    # 데이터프레임 딕셔너리 생성
    dfs = {f"{name}_df": pd.read_excel(f'data/{name}_data.xlsx') for name in df_files}
    
    # date 열 삭제 및 날짜 형식 변환, 중복 제거
    for df_name, df in dfs.items():
        df['date'] = pd.to_datetime(df['date'])
        df.drop_duplicates(subset=['date'], keep='first', inplace=True)
        # 2025-05-14 데이터 삭제
        df.drop(df[df['date'] == '2025-05-14'].index, inplace=True)

    # 광고 데이터 로드
    ad_df = pd.read_csv('data/ads/ad_2025_02_2025_05.csv')
    ad_df['date'] = pd.to_datetime(ad_df['date'])
    ad_df['est_cost'] = ad_df['est_cost'].fillna(0).astype(int)
    ad_df['target_count'] = ad_df['target_count'].fillna(0).astype(int)

    # uv_df와 ad_df 병합
    uv_df = dfs['uv_df'].merge(ad_df, on='date', how='left')
    
    # 결측치 처리
    uv_df['campaign_name'] = uv_df['campaign_name'].fillna('')
    uv_df['campaign_desc'] = uv_df['campaign_desc'].fillna('')
    uv_df['est_cost'] = uv_df['est_cost'].fillna(0)
    uv_df['target_count'] = uv_df['target_count'].fillna(0)

    # resolutionDashboard_df와 uv_df 병합
    uv_df = uv_df.merge(dfs['resolutionDashboard_df'][['date', '해상도', '비율']], on='date', how='left')
    uv_df['해상도'] = uv_df['해상도'].fillna('')
    uv_df['비율'] = uv_df['비율'].fillna(0)

    # 추가 변수 생성
    uv_df['has_ad'] = (uv_df['est_cost'] > 0).astype(int)
    uv_df['is_after_0326'] = (uv_df['date'] >= '2025-03-26').astype(int)
    uv_df['is_weekend'] = uv_df['date'].dt.dayofweek.isin([5, 6]).astype(int)
    uv_df['day_of_week'] = uv_df['date'].dt.day_name()
    uv_df['prev_day_visitors'] = uv_df['방문자수'].shift(1)

    # 일별 광고비 집계
    daily_cost = uv_df.groupby('date')['est_cost'].sum().reset_index()
    daily_cost.columns = ['date', 'daily_cost']
    uv_df = pd.merge(uv_df, daily_cost, on='date', how='left')

    return uv_df, dfs

# 데이터 로드
with st.spinner("데이터를 불러오는 중입니다. 잠시만 기다려주세요..."):
    uv_df, dfs = load_data()

# 사이드바 설정
st.sidebar.title("네이버 애널리틱스 대시보드")
st.sidebar.markdown("---")

# 메인 대시보드
st.title("네이버 애널리틱스 대시보드")

# 분석 기간 표시
start_date = uv_df['date'].min().strftime('%Y년 %m월 %d일')
end_date = uv_df['date'].max().strftime('%Y년 %m월 %d일')
st.markdown(f"### 분석 기간: {start_date} ~ {end_date}")

# 1. 기본 통계
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("총 방문자수", f"{uv_df['방문자수'].sum():,.0f}명")
with col2:
    st.metric("평균 방문자수", f"{uv_df['방문자수'].mean():,.0f}명")
with col3:
    st.metric("최대 방문자수", f"{uv_df['방문자수'].max():,.0f}명")
with col4:
    st.metric("총 광고비", f"{uv_df['est_cost'].sum():,.0f}원")

# 2. 방문자수 추이 그래프
st.subheader("방문자수 추이와 광고 효과 분석")

# 기본 그래프 생성
fig = go.Figure()

# 주말 배경 표시
for idx, row in uv_df[uv_df['is_weekend'] == 1].iterrows():
    fig.add_vrect(
        x0=row['date'],
        x1=row['date'],
        fillcolor="#FADBD8",
        opacity=0.3,
        layer="below",
        line_width=0,
        name='주말'
    )

# 일별 방문자수 시각화
fig.add_trace(go.Scatter(
    x=uv_df['date'],
    y=uv_df['방문자수'],
    mode='lines+markers',
    name='일별 방문자수',
    line=dict(color='#2E86C1', width=2),
    marker=dict(size=8, color='#2E86C1'),
    hovertemplate='날짜: %{x}<br>방문자수: %{y:,.0f}명<extra></extra>'
))

# 광고비 시각화 (보조 Y축)
fig.add_trace(go.Bar(
    x=uv_df['date'],
    y=uv_df['est_cost'],
    name='광고비',
    marker_color='rgba(255, 0, 0, 0.5)',
    yaxis='y2',
    hovertemplate='날짜: %{x}<br>광고비: %{y:,.0f}원<extra></extra>'
))

# 광고 집행일 표시
ad_dates = uv_df[uv_df['est_cost'] > 0]  # 광고비가 있는 날짜만 선택
for idx, row in ad_dates.iterrows():
    fig.add_trace(go.Scatter(
        x=[row['date']],
        y=[row['방문자수']],
        mode='markers',
        marker=dict(
            size=12,
            color='#E74C3C',
            symbol='star',
            line=dict(width=2, color='#C0392B')
        ),
        name='광고 집행일',
        hovertemplate=f"방문자수: {row['방문자수']:,.0f}명<br>채널: {row['category']}<br>광고명: {row['campaign_desc']}<br>광고비: {row['est_cost']:,.0f}원<extra></extra>",
        showlegend=False
    ))

# 레이아웃 설정
fig.update_layout(
    title='일별 방문자수 추이와 광고 효과 분석',
    xaxis_title='날짜',
    yaxis_title='방문자수',
    yaxis2=dict(
        title='광고비',
        overlaying='y',
        side='right',
        showgrid=False,
        range=[0, uv_df['est_cost'].max() * 1.1]  # 광고비 축 범위 조정
    ),
    hovermode='x unified',
    height=800,  # 그래프 높이 증가
    showlegend=True,
    legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=0.01,
        bgcolor='rgba(255, 255, 255, 0.9)',
        bordercolor='#BDC3C7',
        borderwidth=1
    )
)

# 범례에 광고 집행일 설명 추가
fig.add_trace(go.Scatter(
    x=[None],
    y=[None],
    mode='markers',
    marker=dict(
        size=12,
        color='#E74C3C',
        symbol='star',
        line=dict(width=2, color='#C0392B')
    ),
    name='광고 집행일',
    showlegend=True
))

st.plotly_chart(fig, use_container_width=True)

# 3. 요일별 분석
st.subheader("요일별 방문자수 분석")

# 요일별 평균 방문자수 계산
daily_avg = uv_df.groupby('day_of_week')['방문자수'].mean().reindex(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])

# 요일별 방문자수 시각화
fig_daily = go.Figure()

# 평일과 주말 색상 구분
colors = ['#2E86C1'] * 5 + ['#E74C3C'] * 2

fig_daily.add_trace(go.Scatter(
    x=daily_avg.index,
    y=daily_avg.values,
    mode='lines+markers',
    line=dict(color='#2E86C1', width=3),
    marker=dict(size=10, color=colors),
    text=[f'{v:,.0f}명' for v in daily_avg.values],
    textposition='top center',
    hovertemplate='요일: %{x}<br>평균 방문자수: %{y:,.0f}명<extra></extra>'
))

# 레이아웃 설정
fig_daily.update_layout(
    title='요일별 평균 방문자수',
    xaxis_title='요일',
    yaxis_title='평균 방문자수',
    showlegend=False,
    height=400,
    yaxis=dict(
        gridcolor='#ECF0F1',
        gridwidth=1
    ),
    plot_bgcolor='white'
)

# 평균선 추가
mean_visitors = daily_avg.mean()
fig_daily.add_hline(
    y=mean_visitors,
    line_dash="dash",
    line_color="gray",
    annotation_text=f"평균: {mean_visitors:,.0f}명",
    annotation_position="right"
)

st.plotly_chart(fig_daily, use_container_width=True)
