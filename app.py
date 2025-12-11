import streamlit as st
import pandas as pd

# ==========================================
# 1. 실제 데이터 로드 (20만 개 DB 연결)
# ==========================================
@st.cache_data
def load_data():
    # 업로드하신 파일명 그대로 입력 (확장자 주의)
    file_name = '20251121_가공식품DB_205420건_CSV.csv'
    
    try:
        # 공공데이터는 보통 cp949 인코딩을 사용합니다.
        df = pd.read_csv(file_name, encoding='cp949')
    except:
        # 실패 시 utf-8로 재시도
        df = pd.read_csv(file_name, encoding='utf-8')
    
    # 분석에 필요한 핵심 컬럼만 선택 (컬럼명이 다르면 수정 필요)
    # 20만 개 중 필요한 정보만 남겨서 속도를 높입니다.
    required_cols = ['식품명', '식품유형', '당류(g)', '단백질(g)', '열량(kcal)', '탄수화물(g)', '제조사명']
    
    # 데이터에 해당 컬럼이 있는지 확인 후 필터링
    available_cols = [c for c in df.columns if c in required_cols]
    df = df[available_cols]
    
    # 결측치(빈 값)는 0으로 채움
    df = df.fillna(0)
    return df

# 데이터 불러오기 시도
try:
    food_db = load_data()
    db_status = "✅ 205,420개 식품 데이터 연결 성공"
except Exception as e:
    db_status = f"⚠️ 데이터 로드 실패: {e}"
    food_db = pd.DataFrame() # 빈 데이터프레임 생성

# ==========================================
# 2. V2 그룹 분류 로직 (4단계)
# ==========================================
def classify_group(score):
    """
    사용자 점수에 따라 4개 그룹으로 분류
    (txt 파일의 정의에 맞춰 기준 점수를 조정하세요)
    """
    if score <= 20:
        return "Group A", "Healthy (건강 유지형)", "안정", "blue"
    elif score <= 40:
        return "Group B", "Glucose Spike (혈당 스파이크형)", "주의", "green"
    elif score <= 70:
        return "Group C", "Pre-Diabetes (전단계 관리형)", "경고", "orange"
    else:
        return "Group D", "Diabetes (당뇨 집중 케어형)", "위험", "red"

def get_recommendations(group, db):
    """
    그룹별 맞춤 식품 필터링 로직
    """
    if db.empty:
        return pd.DataFrame()

    if group == "Group A":
        # 건강 유지: 당류 15g 미만 + 단백질 5g 이상 (맛과 건강 밸런스)
        filtered = db[(db['당류(g)'] < 15) & (db['단백질(g)'] >= 5)]
        desc = "당류 15g 미만, 고단백 간식"
        
    elif group == "Group B":
        # 스파이크 방지: 당류 5g 미만 (저당)
        filtered = db[db['당류(g)'] <= 5]
        desc = "당류 5g 이하, 급상승 방지 간식"
        
    elif group == "Group C":
        # 전단계 관리: 당류 2g 미만 (초저당)
        filtered = db[db['당류(g)'] <= 2]
        desc = "당류 2g 이하, 엄격 관리 제품"
        
    else: # Group D
        # 당뇨 케어: 당류 1g 미만 (Zero) + 탄수화물 제한
        filtered = db[(db['당류(g)'] < 1) & (db['탄수화물(g)'] < 10)]
        desc = "당류 0g (Zero Sugar), 탄수화물 제한"

    # 결과 중 랜덤으로 5개 추천
    if len(filtered) > 0:
        return filtered.sample(n=min(5, len(filtered))), desc
    else:
        return pd.DataFrame(), desc

# ==========================================
# 3. 앱 화면 구성 (UI)
# ==========================================
st.set_page_config(page_title="혈당마스터 V2.0", page_icon="🩸")

st.title("🩸 혈당 마스터 V2.0")
st.caption(db_status) # 데이터 연결 상태 표시

st.divider()

# 간단 설문 (문항은 V2 기획에 맞춰 수정 가능)
with st.form("survey_v2"):
    st.subheader("📝 건강 설문 (V2)")
    
    q1 = st.slider("1. 일주일 중 야식이나 단 간식을 먹는 횟수는?", 0, 10, 2)
    q2 = st.slider("2. 식사 후 졸음이 쏟아지는 정도는? (0: 없음 ~ 10: 기절)", 0, 10, 3)
    q3 = st.radio("3. 가족 중 당뇨 환자가 있나요?", ["없음 (0)", "한 분 (10)", "두 분 이상 (20)"])
    q4 = st.radio("4. 최근 건강검진 결과는?", ["정상 (0)", "주의 단계 (10)", "당뇨 진단/약 복용 (30)"])
    
    submitted = st.form_submit_button("🔍 내 맞춤 그룹 & 상품 찾기")

if submitted:
    # 점수 계산
    score_q3 = 0 if "없음" in q3 else (10 if "한 분" in q3 else 20)
    score_q4 = 0 if "정상" in q4 else (10 if "주의" in q4 else 30)
    total_score = (q1 * 3) + (q2 * 2) + score_q3 + score_q4
    
    # 1. 그룹 분류 결과
    g_code, g_name, status, color = classify_group(total_score)
    
    st.markdown(f"""
        <div style='background-color:#f0f2f6; padding:20px; border-radius:10px; border-left: 5px solid {color}'>
            <h2 style='color:{color}; margin:0;'>{g_name}</h2>
            <p style='font-size:18px; margin-top:5px;'>당신의 상태는 <b>'{status}'</b> 단계입니다.</p>
        </div>
    """, unsafe_allow_html=True)
    
    # 2. 상품 추천 결과
    st.write("")
    st.subheader(f"📦 {g_code} 맞춤 큐레이션")
    
    with st.spinner('20만 개 식품 데이터 분석 중...'):
        rec_df, rule = get_recommendations(g_code, food_db)
    
    if not rec_df.empty:
        st.info(f"💡 추천 기준: **{rule}**")
        for idx, row in rec_df.iterrows():
            st.success(f"**{row['식품명']}** ({row['제조사명']}) \n\n "
                       f"🍬 당류: {row['당류(g)']}g | 💪 단백질: {row['단백질(g)']}g | 🔥 {row['열량(kcal)']} kcal")
    else:
        st.warning("조건에 맞는 상품 데이터가 없습니다. (CSV 파일을 확인해주세요)")