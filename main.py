import os
import pdfplumber
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from collections import Counter
import re
import base64
from io import BytesIO
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import shutil
from konlpy.tag import Okt
from typing import List, Optional

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

UPLOAD_DIR = "upload"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

okt = Okt()

def get_default_stopwords():
    return [
        '있다', '없다', '하다', '되다', '이다', '그', '저', '이', '거기', '저기', '것', '나', '너', '우리', '너희', '그들',
        '그리고', '하지만', '그러나', '그래서', '때문에', '즉', '만약', '그렇다면', '그리고', '그러므로', '그러나', '또한', 
        '또', '그래도', '때', '어디', '어느', '어떻게', '누구', '왜', '무엇', '의', '가', '이', '은', '를', '에', '로', 
        '에게', '와', '과', '도', '만', '뿐', '까지', '에서', '까지', '하고', '이며', '처럼', '같이', '보다', '보다도', 
        '오', '여', '또는', '아니면', '그리고', '즉', '앞', '뒤', '위', '아래', '안', '밖', '좌', '우', '옆', '안쪽', '밖쪽', 
        '및', '더', '덜', '가장', '그때', '지금', '때', '언제', '날', '연', '월', '일', '년', '시간', '분', '초', '저번', '다음',
        '이후', '전', '후', '시작', '끝', '동안', '사이', '과거', '현재', '미래'
    ]

def extract_text_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        all_text = ''
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                all_text += text + '\n'
    return all_text

def analyze_word_frequency(text: str, stopwords: List[str] = None):
    if stopwords is None:
        stopwords = []
    
    # 형태소 분석
    tokens = okt.morphs(text)
    
    # 불용어 제거
    filtered_tokens = [word for word in tokens if word not in stopwords and len(word) > 1]
    
    # 단어 빈도 계산
    word_count = Counter(filtered_tokens)
    
    # 상위 10개 추출
    return word_count.most_common(10)

def create_frequency_plot(word_counts):
    import matplotlib.pyplot as plt
    import platform
    
    # 운영체제별 한글 폰트 설정
    if platform.system() == 'Windows':
        plt.rc('font', family='Malgun Gothic')
    elif platform.system() == 'Darwin':  # macOS
        plt.rc('font', family='AppleGothic')
    else:  # Linux
        plt.rc('font', family='NanumGothic')
    
    # 그래프에서 마이너스 기호가 깨지는 것을 방지
    plt.rc('axes', unicode_minus=False)
    
    words, counts = zip(*word_counts)
    
    plt.figure(figsize=(12, 6))
    plt.bar(range(len(words)), counts, color='skyblue')
    plt.xticks(range(len(words)), words, rotation=45, ha='right')
    plt.title('상위 10개 단어 빈도')
    plt.xlabel('단어')
    plt.ylabel('빈도')
    
    # 여백 조정
    plt.tight_layout()
    
    img = BytesIO()
    plt.savefig(img, format='png', dpi=300, bbox_inches='tight')
    plt.close()
    img.seek(0)
    
    return base64.b64encode(img.getvalue()).decode()
@app.post("/analyze/{filename}")
async def analyze_file(
    filename: str, 
    analysis_type: str,
    stopword_option: Optional[str] = None,
    custom_stopwords: Optional[str] = None
):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        return JSONResponse(
            status_code=404,
            content={"message": "File not found"}
        )

    try:
        text = extract_text_from_pdf(file_path)
        
        if analysis_type == "wordcloud":
            wordcloud_img = create_wordcloud(text)
            return {
                "type": "wordcloud",
                "image": wordcloud_img,
                "debug_info": {
                    "total_words": len(text.split())
                }
            }
        
        elif analysis_type == "frequency":
            stopwords = []
            if stopword_option == "default":
                stopwords = get_default_stopwords()
            elif stopword_option == "custom" and custom_stopwords:
                stopwords = get_default_stopwords() + [word.strip() for word in custom_stopwords.split(',')]
                
            word_counts = analyze_word_frequency(text, stopwords)
            plot_image = create_frequency_plot(word_counts)
            
            return {
                "type": "frequency",
                "image": plot_image,
                "word_counts": word_counts
            }
            
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"message": f"Analysis failed: {str(e)}"}
        )

@app.get("/")
async def get():
    return FileResponse('static/index.html')

def extract_text_from_pdf(pdf_path):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            all_text = ''
            total_pages = len(pdf.pages)
            
            print(f"총 페이지 수: {total_pages}")  # 디버깅용 출력
            
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text:
                    all_text += f"\n[Page {page_num}]\n" + text
                print(f"페이지 {page_num} 처리 완료. 추출된 텍스트 길이: {len(text) if text else 0}")  # 디버깅용 출력
                
            print(f"전체 추출된 텍스트 길이: {len(all_text)}")  # 디버깅용 출력
            return all_text
    except Exception as e:
        print(f"PDF 텍스트 추출 중 오류 발생: {str(e)}")  # 디버깅용 출력
        raise e

def create_wordcloud(text):
    words = re.findall(r'\b[가-힣a-zA-Z0-9]+\b', text)
    word_string = ' '.join(words)

    wordcloud = WordCloud(
        font_path='C:/Windows/Fonts/malgun.ttf',
        width=800, 
        height=600, 
        background_color='white'
    ).generate(word_string)

    img = BytesIO()
    plt.figure(figsize=(10, 6))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.savefig(img, format='png', bbox_inches='tight')
    plt.close()
    img.seek(0)
    
    return base64.b64encode(img.getvalue()).decode()

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {"filename": file.filename, "status": "success"}
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"message": f"Upload failed: {str(e)}"}
        )

@app.post("/analyze/{filename}")
async def analyze_file(filename: str, analysis_type: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        return JSONResponse(
            status_code=404,
            content={"message": "File not found"}
        )

    try:
        print(f"파일 분석 시작: {filename}")  # 디버깅용 출력
        text = extract_text_from_pdf(file_path)
        
        print(f"추출된 전체 텍스트 미리보기:\n{text[:500]}...")  # 디버깅용 출력
        
        if analysis_type == "wordcloud":
            words = re.findall(r'\b[가-힣a-zA-Z0-9]+\b', text)
            print(f"추출된 단어 수: {len(words)}")  # 디버깅용 출력
            print(f"단어 샘플: {words[:20]}")  # 디버깅용 출력
            
            wordcloud_img = create_wordcloud(text)
            return {
                "type": "wordcloud",
                "image": wordcloud_img,
                "text": text,
                "debug_info": {
                    "total_text_length": len(text),
                    "total_words": len(words),
                    "word_sample": words[:20]
                }
            }
    except Exception as e:
        print(f"분석 중 오류 발생: {str(e)}")  # 디버깅용 출력
        return JSONResponse(
            status_code=400,
            content={"message": f"Analysis failed: {str(e)}"}
        )

@app.on_event("shutdown")
async def shutdown_event():
    # 서버 종료시 업로드 폴더 정리
    shutil.rmtree(UPLOAD_DIR, ignore_errors=True)