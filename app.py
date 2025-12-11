import streamlit as st
import pandas as pd
import os
import plotly.express as px  # 차트 그리는 도구 추가

# ==========================================
# 1. 스마트 데이터 로드 (유지)
# ==========================================
@st.cache_data
def load_data():
    current_files = os.listdir('.')
    target_file = None
    for f in current_files:
        if f.endswith('.csv') or f.endswith('.zip'):
            target_file = f
            break
    
    if target_file is None: return pd.DataFrame()

    try: df = pd.read_csv(target_file, encoding='cp949')
    except:
        try: df = pd.read_csv(target_file, encoding='utf-8')
        except: df = pd.read_csv(target_file, encoding='euc-kr')

    cols_candidates = {
        '식품명': ['식품명', '제품명'],
        '당류': ['당류(g)', '당류'],
        '단백질': ['단백질(g)', '단백질'],
        '열량': ['열량(kcal)', '열량'],
        '제조사': ['제조사명', '제조사']
    }
    
    selected_cols = []
    for key, candidates in cols_candidates.items():
        for cand in candidates:
            if cand in df.columns:
                selected_cols.append(cand)
                break
    
    if len(selected_cols) > 0:
        df = df[selected_cols].fillna(0)
    return df

try:
    food_db = load_data()
    db_status = "✅ DB 연결됨" if not food_db.empty else "⚠️ DB 없음"
except:
    food_db = pd.DataFrame()
    db_status = "⚠️ DB 에러"

# ==========================================
# 2. 설문 문항 (20개 유지)
# ==========================================
survey_sections = {
    "식습관 (Diet)": [
        {"q": "탄수화물(밥/빵/면) 위주 식사", "max": 5},
        {"q": "식사 속도 빠름 (15분 이내)", "type": "binary", "opts": {"No":0, "Yes":5}},
        {"q": "단 음료(믹스커피/주스) 매일 섭취", "max": 5},
        {"q": "음주 빈도", "type": "select", "opts": {"안함":0, "1~2회":3, "3회+":5}},
        {"q": "배불러도 계속 먹음", "type": "binary", "opts": {"No":0, "Yes":5}},
        {"q": "야식 (밤 9시 이후)", "max": 5}
    ],
    "신체증상 (Body)": [
        {"q": "식후 식곤증", "max": 5},
        {"q": "급격한 체중 변화", "type": "binary", "opts": {"No":0, "Yes":5}},
        {"q": "잦은 갈증/다음", "type": "binary", "opts": {"No":0, "Yes":5}},
        {"q": "잦은 소변/거품", "type": "binary", "opts": {"No":0, "Yes":5}},
        {"q": "상처 회복 느림/피부 가려움", "type": "binary", "opts": {"No":0, "Yes":5}},
        {"q": "손발 저림", "type": "binary", "opts": {"No":0, "Yes":5}}
    ],
    "생활습관 (Life)": [
        {"q": "운동 부족 (주 2회 미만)", "type": "select", "opts": {"운동함":0, "가끔":3, "안함":5}},
        {"q": "스트레스 수준", "max": 5},
        {"q": "수면 불규칙", "type": "select", "opts": {"규칙적":0, "보통":3, "불규칙":5}},
        {"q": "좌식 생활 시간 긺", "type": "binary", "opts": {"No":0, "Yes":5}}
    ],
    "가족력/기타 (History)": [
        {"q": "가족력 (당뇨)", "type": "select", "opts": {"없음":0, "1명":5, "2명+":10}},
        {"q": "과거 혈당 주의 판정", "type": "binary", "opts": {"No":0, "Yes":5}},
        {"q": "혈압/고지혈증 약 복용", "type": "binary", "opts": {"No":0, "Yes":5}},
        {"q": "연령대", "type": "select", "opts": {"2030":0, "4050":3, "60+":5}}
    ]
}

# ==========================================
# 3. 로직 함수
# ==========================================
def classify_group(score):
    if score <= 20: return "Group A", "Healthy (건강 유지형)", "blue"
    elif score <= 45: return "Group B", "Glucose Spike (혈당 스파이크형)", "green"
    elif score <= 70: return "Group C", "Pre-Diabetes (전단계 관리형)", "orange"
    else: return "Group D", "Diabetes (당뇨 집중 케어형)", "red"

def get_recommendations(group, db):
    if db.empty: return pd.DataFrame(), "데이터 없음"
    col_sugar = [c for c in db.columns if '당류' in c][0]
    
    if group == "Group A":
        filtered = db[(db[col_sugar] < 15) & (db['단백질(g)'] >= 5)]
        desc = "밸런스 간식 (당류 15g↓)"
    elif group == "Group B":
        filtered = db[db[col_sugar] < 10]
        desc = "스파이크 방지 (당류 10g↓)"
    elif group == "Group C":
        filtered = db[db[col_sugar] <= 5]
        desc = "전단계 관리 (당류 5g↓)"
    else: 
        filtered = db[db[col_sugar] < 1]
        desc = "집중 케어 (Zero Sugar)"

    return (filtered.sample(n=min(5, len(filtered))), desc) if len(filtered) > 0 else (pd.DataFrame(), desc)

# ==========================================
# 4. UI 구성 (차트 추가됨)
# ==========================================
st.set_page_config(page_title="혈당마스터 리포트", page_icon="📊", layout="wide")

# 사이드바 (메뉴)
with st.sidebar:
    st.title("🩸 혈당 마스터")
    st.info(f"DB 상태: {db_status}")
    st.write("---")
    st.write("이 서비스는 '가공식품 DB'를 기반으로 맞춤형 간식을 추천합니다.")

st.title("📊 나만의 혈당 건강 리포트")
st.caption("20개 정밀 문항 분석 및 시각화 결과 제공")

# 점수 저장용 변수
category_scores = {}
total_score = 0

with st.form("survey_form_v3"):
    # 2열로 배치해서 스크롤 줄이기
    col1, col2 = st.columns(2)
    
    # 딕셔너리를 리스트로 변환해서 인덱스로 접근 (좌우 배치용)
    sections = list(survey_sections.items())
    
    # 왼쪽 컬럼 (Part 1, 2)
    with col1:
        for i in range(0, 2):
            section_name, questions = sections[i]
            st.subheader(section_name)
            current_sec_score = 0
            for j, q in enumerate(questions):
                key = f"{section_name}_{j}"
                if q.get('type') == 'binary':
                    val = st.radio(q['q'], list(q['opts'].keys()), horizontal=True, key=key)
                    score = q['opts'][val]
                elif q.get('type') == 'select':
                    val = st.selectbox(q['q'], list(q['opts'].keys()), key=key)
                    score = q['opts'][val]
                else:
                    score = st.slider(q['q'], 0, q['max'], 0, key=key)
                current_sec_score += score
            category_scores[section_name] = current_sec_score
            st.write("---")

    # 오른쪽 컬럼 (Part 3, 4)
    with col2:
        for i in range(2, 4):
            section_name, questions = sections[i]
            st.subheader(section_name)
            current_sec_score = 0
            for j, q in enumerate(questions):
                key = f"{section_name}_{j}"
                if q.get('type') == 'binary':
                    val = st.radio(q['q'], list(q['opts'].keys()), horizontal=True, key=key)
                    score = q['opts'][val]
                elif q.get('type') == 'select':
                    val = st.selectbox(q['q'], list(q['opts'].keys()), key=key)
                    score = q['opts'][val]
                else:
                    score = st.slider(q['q'], 0, q['max'], 0, key=key)
                current_sec_score += score
            category_scores[section_name] = current_sec_score
            st.write("---")

    submit = st.form_submit_button("🔍 분석 결과 및 리포트 보기", type="primary", use_container_width=True)

if submit:
    # 총점 계산
    total_score = sum(category_scores.values())
    g_code, g_name, color = classify_group(total_score)
    
    st.divider()
    
    # [시각화] 레이아웃: 왼쪽은 점수판, 오른쪽은 차트
    res_col1, res_col2 = st.columns([1, 1])
    
    with res_col1:
        st.markdown(f"### 당신의 유형: <span style='color:{color}'>{g_name}</span>", unsafe_allow_html=True)
        st.metric(label="총 위험도 점수", value=f"{total_score}점", delta="-관리 필요" if total_score > 40 else "양호")
        st.write(f"**{g_name}**에 해당하는 맞춤 솔루션을 제공합니다.")
    
    with res_col2:
        # 방사형 차트 (Radar Chart) 그리기
        df_chart = pd.DataFrame({
            'Category': list(category_scores.keys()),
            'Score': list(category_scores.values())
        })
        fig = px.line_polar(df_chart, r='Score', theta='Category', line_close=True, range_r=[0, 30])
        fig.update_traces(fill='toself', line_color=color)
        fig.update_layout(margin=dict(t=20, b=20, l=20, r=20)) # 여백 줄이기
        st.plotly_chart(fig, use_container_width=True)

    # 상품 추천 섹션
    st.subheader(f"📦 {g_code} 맞춤 큐레이션")
    rec_df, rule = get_recommendations(g_code, food_db)
    
    if not rec_df.empty:
        st.info(f"💡 추천 알고리즘 기준: {rule}")
        # 3열로 카드 배치
        rec_cols = st.columns(3)
        for i, (idx, row) in enumerate(rec_df.iterrows()):
            with rec_cols[i % 3]:
                st.markdown(f"""
                <div style="border:1px solid #ddd; padding:15px; border-radius:10px; height:200px;">
                    <h4>{row['식품명']}</h4>
                    <small>{row['제조사명']}</small>
                    <hr>
                    <p>🍬 당류: {row[rec_df.columns[2]]}g</p>
                    <p>💪 단백질: {row['단백질(g)']}g</p>
                </div>
                """, unsafe_allow_html=True)