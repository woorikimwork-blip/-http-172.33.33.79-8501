# [수정 전] 원래 코드
# df = pd.read_csv('20251121_가공식품DB_205420건_CSV.csv', encoding='cp949')

# 👇 [수정 후] 이 코드로 덮어쓰세요
@st.cache_data
def load_data():
    # 1. 파일명 확인: 업로드하신 ZIP 파일의 정확한 이름으로 바꿔주세요.
    # 예시: '20251121_가공식품DB_205420건_CSV.zip'
    zip_filename = '20251121_가공식품DB_205420건_CSV.zip' 

    try:
        # zip 파일 안에 있는 CSV를 바로 읽습니다. (인코딩은 cp949 또는 utf-8 시도)
        df = pd.read_csv(zip_filename, encoding='cp949')
    except:
        df = pd.read_csv(zip_filename, encoding='utf-8')

    # (이 아래는 기존과 동일합니다)
    cols = ['식품명', '제조사명', '영양성분함량기준용량', '열량(kcal)', '탄수화물(g)', '당류(g)', '단백질(g)', '지방(g)']
    valid_cols = [c for c in cols if c in df.columns]
    df = df[valid_cols].fillna(0)
    return df