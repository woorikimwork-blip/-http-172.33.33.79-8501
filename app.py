import streamlit as st
import pandas as pd
import os

# ==========================================
# 1. 스마트 데이터 로드 (파일 자동 찾기)
# ==========================================
@st.cache_data
def load_data():
    # 현재 폴더에 있는 모든 파일 목록을 봅니다.
    current_files = os.listdir('.')
    
    # .csv 또는 .zip으로 끝나는 파일을 찾습니다.
    target_file = None
    for f in current_files:
        if f.endswith('.csv') or f.endswith('.zip'):
            target_file = f
            break
    
    # 파일을 못 찾았으면 에러 메시지 띄우기
    if target_file is None:
        st.error(f"🚨 데이터 파일을 못 찾겠습니다! 현재 파일 목록: {current_files}")
        return pd.DataFrame()

    # 찾은 파일 읽기 (ZIP이든 CSV든 알아서 처리)
    try:
        # 1차 시도: cp949 (한글 윈도우 기본)
        df = pd.read_csv(target_file, encoding='cp949')
    except:
        try:
            # 2차 시도: utf-8
            df = pd.read_csv(target_file, encoding='utf-8')
        except:
             # 3차 시도: euc-kr
            df = pd.read_csv(target_file, encoding='euc-kr')

    # 필요한 컬럼만 선택
    # (실제 데이터에 있는 컬럼 이름과 최대한 매칭)
    # 다운받으신 파일의 실제 컬럼명을 확인해서 여기 수정이 필요할 수 있습니다.
    cols_candidates = {
        '식품명': ['식품명', '제품명', '음식명'],
        '당류': ['당류(g)', '당류', 'sugar'],
        '단백질': ['단백질(g)', '단백질', 'protein'],
        '열량': ['열량(kcal)', '에너지(kcal)', '열량'],
        '제조사': ['제조사명', '제조사', '업체명']
    }
    
    selected_cols = []
    # 데이터프레임의 컬럼 이름을 하나씩 확인하며 매칭
    for key, candidates in cols_candidates.items():
        for cand in candidates:
            if cand in df.columns:
                selected_cols.append(cand)
                break
    
    if len(selected_cols) > 0:
        df = df[selected_cols].fillna(0)
    
    return df

# 데이터 로딩 실행
try:
    food_db = load_data()
    if not food_db.empty:
        db_status = f"✅ 데이터 연결 성공! ({len(food_db):,}개)"
    else:
        db_status = "⚠️ 데이터가 비어있습니다."
except Exception as e:
    db_status = f"⚠️ 로딩 에러: {e}"
    food_db = pd.DataFrame()

# ==========================================
# 2. 그룹 분류 및 추천 로직
# ==========================================
def classify_group(score):
    if score <= 20: return "Group A", "Healthy (건강 유지형)", "blue"
    elif score <= 40: return "Group B", "Glucose Spike (혈당 스파이크형)", "green"
    elif score <= 70: return "Group C", "Pre-Diabetes (전단계 관리형)", "orange"
    else: return "Group D", "Diabetes (당뇨 집중 케어형)", "red"

def get_recommendations(group, db):
    if db.empty:
        return pd.DataFrame(), "데이터 없음"

    # 컬럼명이 파일마다 다를 수 있어 유연하게 찾기
    col_sugar = [c for c in db.columns if '당류' in c][0]
    
    if group == "Group A":
        filtered = db[db[col_sugar] < 15]
        desc = "당류 15g 미만 간식"
    elif group == "Group B":
        filtered = db[db[col_sugar] <= 5]
        desc = "당류 5g 이하 (저당)"
    elif group == "Group C":
        filtered = db[db[col_sugar] <= 2]
        desc = "당류 2g 이하 (초저당)"
    else: 
        filtered = db[db[col_sugar] < 1]
        desc = "당류 0g (Zero Sugar)"

    if len(filtered) > 0:
        return filtered.sample(n=min(5, len(filtered))), desc
    else:
        return pd.DataFrame(), desc

# ==========================================
# 3. 앱 화면 (UI)
# ==========================================
st.set_page_config(page_title="혈당마스터 V2.0", page_icon="🩸")
st.title("🩸 혈당 마스터 V2.0")
st.caption(db_status) # 상태 메시지 확인용

# 만약 파일을 못 찾았으면 화면에 파일 목록을 보여줌 (디버깅용)
if "데이터 파일을 못 찾겠습니다" in str(db_status):
    st.error("GitHub에 파일이 없거나 이름이 다릅니다. 아래 파일 목록을 확인하세요.")
    st.code(os.listdir('.'))

st.divider()

with st.form("survey_v2"):
    st.subheader("📝 건강 설문")
    q1 = st.slider("단 음식/야식 빈도", 0, 10, 2)
    q2 = st.slider("식곤증 정도", 0, 10, 3)
    submitted = st.form_submit_button("결과 보기")

if submitted:
    total_score = (q1 * 5) + (q2 * 5)
    g_code, g_name, color = classify_group(total_score)
    
    st.markdown(f"<h3 style='color:{color}'>{g_name}</h3>", unsafe_allow_html=True)
    
    rec_df, rule = get_recommendations(g_code, food_db)
    
    if not rec_df.empty:
        st.info(f"추천 기준: {rule}")
        st.dataframe(rec_df) # 표 형태로 보여주기
    else:
        st.warning("조건에 맞는 상품이 없습니다.")