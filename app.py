import streamlit as st
import pandas as pd

# ==========================================
# 1. 데이터 세팅 (Data Setup)
# ==========================================

# (1) 진단 설문 리스트 (예시 7문항, 실제 20문항으로 확장 가능)
questions = [
    {"q": "부모님 중 당뇨병 환자가 있으신가요?", "options": {"없음": 0, "한 분": 10, "두 분 이상": 20}},
    {"q": "주 3회 이상 야식을 드시나요?", "options": {"아니오": 0, "가끔": 5, "자주 먹음": 10}}, #  야식 관련 Stage 2 특징
    {"q": "식사 후 급격한 졸음(식곤증)이 오나요?", "options": {"전혀 없음": 0, "가끔": 5, "매우 심함": 10}},
    {"q": "평소 밥, 빵, 면 위주의 식사를 하시나요?", "options": {"아니오": 0, "보통": 5, "그렇다": 10}},
    {"q": "최근 1년 내 체중 변화가 급격한가요?", "options": {"변화 없음": 0, "조금 증가": 5, "급격히 증가": 10}},
    {"q": "평소 물보다 주스나 탄산음료를 즐기시나요?", "options": {"아니오": 0, "가끔": 5, "매일 마심": 10}},
    {"q": "주 3회 이상 30분씩 운동을 하시나요?", "options": {"규칙적임": 0, "불규칙함": 5, "거의 안 함": 10}},
]

# (2) 상품 DB (Stage별 추천 상품)
# PDF에 명시된 상품 구성을 반영했습니다.
products = {
    "Stage 1": [
        {"상품명": "기본 영양 구독팩", "구성": "종합비타민 + 식물성 오메가3", "가격": "39,000원", "특징": "기초 활력 케어"},
        {"상품명": "월간 건강 리포트", "구성": "혈당 데이터 요약", "가격": "구독 포함", "특징": "예방 차원 관리"}
    ],
    "Stage 2": [
        {"상품명": "섬유질 Starter Pack", "구성": "식이섬유 젤리 + 식전 대체식", "가격": "49,000원", "특징": "스파이크 방지"},
        {"상품명": "저당 간식 박스", "구성": "곤약 젤리 + 프로틴 쿠키 (주4회)", "가격": "25,000원", "특징": "오후 3시 입터짐 방지"}
    ],
    "Stage 3": [
        {"상품명": "혈당 119 케어팩", "구성": "고함량 식이섬유 + 크롬/마그네슘", "가격": "89,000원", "특징": "집중 혈당 관리"},
        {"상품명": "저당 식단 정기배송", "구성": "저당 두부면 도시락 (7팩)", "가격": "45,000원", "특징": "탄수화물 제한 식단"}
    ]
}

# ==========================================
# 2. 웹 페이지 UI 구성 (Streamlit)
# ==========================================

st.set_page_config(page_title="혈당 마스터 진단", page_icon="🩸")

# 헤더 섹션
st.title("🩸 혈당 마스터: 나만의 혈당 타입 진단")
st.write("3분 만에 당신의 혈당 위험도를 확인하고, 딱 맞는 솔루션을 처방받으세요.")
st.divider()

# 설문 섹션 (Form)
with st.form("diagnosis_form"):
    st.subheader("📝 라이프스타일 체크")
    
    user_scores = []
    for idx, item in enumerate(questions):
        st.write(f"**Q{idx+1}. {item['q']}**")
        # 라디오 버튼으로 선택지 표시
        choice = st.radio(
            label="답변을 선택하세요",
            options=list(item['options'].keys()),
            key=f"q_{idx}",
            label_visibility="collapsed",
            horizontal=True
        )
        # 선택한 답변의 점수 저장
        user_scores.append(item['options'][choice])
        st.write("") # 여백

    # 제출 버튼
    submitted = st.form_submit_button("🔍 진단 결과 확인하기", use_container_width=True)

# ==========================================
# 3. 결과 처리 로직 (Logic)
# ==========================================

if submitted:
    total_score = sum(user_scores)
    
    # 로딩 효과
    with st.spinner('AI가 고객님의 혈당 유형을 분석 중입니다...'):
        import time
        time.sleep(1.5) # 분석하는 척 연출

    st.divider()
    st.subheader(f"📊 {total_score}점, 진단 결과")

    # 점수별 Stage 판정 로직 
    # (문항 수에 따라 기준 점수는 조정 필요, 여기서는 70점 만점 기준 임의 설정)
    STAGE_1_MAX_SCORE = 15
    STAGE_2_MAX_SCORE = 40

    if total_score <= STAGE_1_MAX_SCORE:
        stage = "Stage 1"
        stage_desc = "Normal (정상 유지형)"
        color = "blue"
        msg = "혈당이 전반적으로 안정적입니다. 지금처럼 꾸준히 관리하세요!"
    elif total_score <= STAGE_2_MAX_SCORE:
        stage = "Stage 2"
        stage_desc = "Pre-Risk (잠재적 위험군)"
        color = "orange"
        msg = "평소엔 괜찮지만 야식이나 폭식으로 '스파이크'가 발생하고 있어요."
    else:
        stage = "Stage 3"
        stage_desc = "High-Risk (고위험군)"
        color = "red"
        msg = "탄수화물 민감도가 매우 높습니다. 적극적인 식단 관리가 필요해요."

    # 결과 카드 표시
    st.markdown(f"""
        <div style="padding:20px; border-radius:10px; background-color:#f0f2f6; border: 2px solid {color};">
            <h2 style="color:{color}; text-align:center;">{stage_desc}</h2>
            <p style="text-align:center; font-size:18px;">"{msg}"</p>
        </div>
    """, unsafe_allow_html=True)

    # 큐레이션 상품 추천
    st.write("")
    st.subheader(f"🎁 {stage_desc} 맞춤 구독 제안")
    
    # 해당 Stage의 상품 리스트 가져오기
    rec_items = products[stage]
    
    # 상품 카드 나열 (2열 배치)
    cols = st.columns(2)
    for i, item in enumerate(rec_items):
        with cols[i % 2]:
            with st.container():
                st.markdown(f"""
                    <div style="
                        border: 1px solid #e0e0e0; 
                        border-radius: 10px; 
                        padding: 15px; 
                        margin-bottom: 10px;
                        background-color: #ffffff;
                        box-shadow: 2px 2px 8px rgba(0,0,0,0.1);
                    ">
                        <h4 style="color:{color}; margin-top:0px; margin-bottom: 10px;">{item['상품명']}</h4>
                        <p style="font-size: 14px; margin-bottom: 5px;">- 구성: {item['구성']}</p>
                        <p style="font-size: 14px; font-weight: bold; color: #4CAF50; margin-bottom: 5px;">- 가격: {item['가격']}</p>
                        <p style="font-size: 12px; color: #6a6a6a; margin-top: 10px;">💡 {item['특징']}</p>
                    </div>
                """, unsafe_allow_html=True)

    # CTA 버튼
    st.button("🚀 이 구성으로 구독 시작하기 (첫 달 50% 할인)", type="primary", use_container_width=True)
    
    st.markdown("---")
    st.info("⚠️ 본 진단 결과 및 상품 추천은 정보 제공을 위한 것이며, 전문 의료 진단 및 처방을 대체할 수 없습니다. 건강 관련 결정은 반드시 의사 또는 전문가와 상담 후 내리시기 바랍니다.")
    
    if st.button("🔄 처음으로 돌아가기"):
        st.session_state.clear()
        st.experimental_rerun()