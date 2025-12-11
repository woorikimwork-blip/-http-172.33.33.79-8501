import streamlit as st
import pandas as pd
import os

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
    
    if target_file is None:
        return pd.DataFrame() # 파일 없음

    try:
        df = pd.read_csv(target_file, encoding='cp949')
    except:
        try: df = pd.read_csv(target_file, encoding='utf-8')
        except: df = pd.read_csv(target_file, encoding='euc-kr')

    # 컬럼 매칭 (당류, 단백질 등)
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
    db_status = "✅ 시스템 정상 가동 중" if not food_db.empty else "⚠️ 데이터 로드 필요"
except:
    food_db = pd.DataFrame()
    db_status = "⚠️ 시스템 점검 중"

# ==========================================
# 2. 설문 문항 정의 (20개 리스트)
# ==========================================
# 각 질문은 선택지에 따라 0점(좋음) ~ 5점(나쁨) 부여
survey_sections = {
    "Part 1. 식습관 (Diet)": [
        {"q": "평소 밥, 빵, 면 등 탄수화물 위주의 식사를 하시나요?", "type": "score", "max": 5},
        {"q": "식사 속도가 15분 이내로 빠른 편인가요?", "type": "binary", "opts": {"아니오":0, "그렇다":5}},
        {"q": "믹스커피, 탄산음료, 주스를 매일 마시나요?", "type": "score", "max": 5},
        {"q": "술을 일주일에 얼마나 드시나요?", "type": "select", "opts": {"안 마심":0, "1~2회":3, "3회 이상":5}},
        {"q": "배가 부른데도 음식을 계속 먹는 경우가 있나요?", "type": "binary", "opts": {"아니오":0, "그렇다":5}},
        {"q": "야식(밤 9시 이후)을 얼마나 자주 드시나요?", "type": "score", "max": 5}
    ],
    "Part 2. 신체 증상 (Symptoms)": [
        {"q": "식사 후 참을 수 없는 졸음(식곤증)이 오나요?", "type": "score", "max": 5},
        {"q": "최근 이유 없이 체중이 급격히 늘거나 줄었나요?", "type": "binary", "opts": {"아니오":0, "그렇다":5}},
        {"q": "갈증이 자주 나서 물을 많이 마시게 되나요?", "type": "binary", "opts": {"아니오":0, "그렇다":5}},
        {"q": "소변 거품이 생기거나 화장실을 자주 가나요?", "type": "binary", "opts": {"아니오":0, "그렇다":5}},
        {"q": "상처가 잘 낫지 않거나 피부가 가려운가요?", "type": "binary", "opts": {"아니오":0, "그렇다":5}},
        {"q": "손발이 저리거나 찌릿한 느낌이 있나요?", "type": "binary", "opts": {"아니오":0, "그렇다":5}}
    ],
    "Part 3. 생활 습관 (Lifestyle)": [
        {"q": "일주일에 30분 이상 운동을 몇 번 하시나요?", "type": "select", "opts": {"3회 이상":0, "1~2회":3, "거의 안 함":5}},
        {"q": "평소 스트레스를 많이 받으시나요?", "type": "score", "max": 5},
        {"q": "수면 시간은 규칙적인가요?", "type": "select", "opts": {"규칙적임":0, "보통":3, "불규칙함":5}},
        {"q": "하루 대부분을 앉아서 보내시나요?", "type": "binary", "opts": {"아니오":0, "그렇다":5}}
    ],
    "Part 4. 가족력 및 기타 (History)": [
        {"q": "부모님 중 당뇨병 환자가 있으신가요?", "type": "select", "opts": {"없음":0, "한 분":5, "두 분 다":10}},
        {"q": "과거 건강검진에서 '혈당 주의' 소견을 받은 적 있나요?", "type": "binary", "opts": {"아니오":0, "그렇다":5}},
        {"q": "고혈압이나 고지혈증 약을 드시나요?", "type": "binary", "opts": {"아니오":0, "그렇다":5}},
        {"q": "현재 본인의 나이대는?", "type": "select", "opts": {"2030":0, "4050":3, "60대 이상":5}}
    ]
}

# ==========================================
# 3. 로직 함수 (100점 만점 기준)
# ==========================================
def classify_group(score):
    # 총점 100점 만점 기준으로 등급 산정
    if score <= 20: return "Group A", "Healthy (건강 유지형)", "blue"
    elif score <= 45: return "Group B", "Glucose Spike (혈당 스파이크형)", "green"
    elif score <= 70: return "Group C", "Pre-Diabetes (전단계 관리형)", "orange"
    else: return "Group D", "Diabetes (당뇨 집중 케어형)", "red"

def get_recommendations(group, db):
    if db.empty: return pd.DataFrame(), "데이터 로딩 중"
    
    col_sugar = [c for c in db.columns if '당류' in c][0]
    
    if group == "Group A":
        # 당류 15g 미만, 단백질 5g 이상
        filtered = db[(db[col_sugar] < 15) & (db['단백질(g)'] >= 5)]
        desc = "맛과 건강의 밸런스 (당류 15g↓)"
    elif group == "Group B":
        # 당류 10g 미만
        filtered = db[db[col_sugar] < 10]
        desc = "혈당 스파이크 방지 (당류 10g↓)"
    elif group == "Group C":
        # 당류 5g 미만
        filtered = db[db[col_sugar] <= 5]
        desc = "철저한 전단계 관리 (당류 5g↓)"
    else: 
        # 당류 1g 미만 (Zero)
        filtered = db[db[col_sugar] < 1]
        desc = "당뇨 집중 케어 (무가당/Zero)"

    if len(filtered) > 0:
        return filtered.sample(n=min(5, len(filtered))), desc
    else:
        return pd.DataFrame(), desc

# ==========================================
# 4. 앱 화면 구성
# ==========================================
st.set_page_config(page_title="혈당마스터 정밀진단", page_icon="🩸")

st.title("🩸 혈당 마스터: 정밀 진단")
st.caption(f"20개 문항으로 분석하는 나만의 혈당 타입 | {db_status}")
st.divider()

total_score = 0

with st.form("survey_form_20"):
    
    for section, questions in survey_sections.items():
        st.subheader(section)
        for i, q_data in enumerate(questions):
            # 질문 표시