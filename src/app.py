from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, db
import google.generativeai as genai
from google import genai
import requests

# 🔹 .env 불러오기
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# 🔹 Gemini API 초기화 (최신 SDK 방식)
# 🔹 Gemini API 초기화
# genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
client = genai.Client(api_key=GEMINI_API_KEY)

# Flask 초기화
app = Flask(__name__)

# 날짜 포맷팅을 위한 필터 추가
@app.template_filter('strftime')
def _jinja2_filter_datetime(date, fmt=None):
    if not fmt:
        fmt = '%Y년 %m월 %d일 %H:%M'
    from datetime import datetime
    return datetime.fromtimestamp(date).strftime(fmt)
# 🔹 Firebase 연결
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # src 폴더 경로
cred_path = os.path.join(BASE_DIR, "firebase_key.json")
db_url = os.getenv("FIREBASE_DB_URL")

# 키 파일 & DB URL 체크
if not os.path.exists(cred_path):
    raise FileNotFoundError(f"❌ Firebase 키 파일을 찾을 수 없습니다: {cred_path}")

if not db_url:
    raise ValueError("❌ 환경변수 FIREBASE_DB_URL이 설정되지 않았습니다. .env 파일을 확인하세요.")

# Firebase 초기화 (중복 방지)
if not firebase_admin._apps:
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred, {"databaseURL": db_url})


# 🔹 메인 페이지
@app.route("/")
def index():
    return render_template("main.html")

# 🔹 메인2 페이지
@app.route("/main2")
def main2():
    user_id = request.args.get('user_id', '')
    ref = db.reference('users')
    user_data = ref.child(user_id).get()
    
    if not user_data:
        user_data = {
            'coins': 100,  # 초기 코인
            'level': 1,    # 초기 레벨
            'exp': 0,      # 초기 경험치
            'achievements': [],  # 업적 목록
            'daily_check': False  # 일일 출석 체크
        }
        ref.child(user_id).set(user_data)
    
    return render_template("main2.html", user_id=user_id, user_data=user_data)

# 🔹 일일 체크인
@app.route('/daily_check', methods=['POST'])
def daily_check():
    user_id = request.form.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': '사용자 ID가 필요합니다.'})
    
    ref = db.reference(f'users/{user_id}')
    user_data = ref.get()
    
    if not user_data:
        return jsonify({'success': False, 'message': '사용자를 찾을 수 없습니다.'})
    
    if user_data.get('daily_check', False):
        return jsonify({'success': False, 'message': '이미 오늘의 출석체크를 완료했습니다.'})
    
    # 코인과 경험치 보상
    user_data['coins'] = user_data.get('coins', 0) + 50
    user_data['exp'] = user_data.get('exp', 0) + 20
    user_data['daily_check'] = True
    
    # 레벨업 체크
    if user_data['exp'] >= user_data['level'] * 100:
        user_data['level'] = user_data.get('level', 1) + 1
        user_data['exp'] = 0
    
    ref.set(user_data)
    return jsonify({
        'success': True,
        'coins': user_data['coins'],
        'exp': user_data['exp'],
        'level': user_data['level']
    })

# 🔹 코인 업데이트
@app.route('/update_coins', methods=['POST'])
def update_coins():
    user_id = request.form.get('user_id')
    amount = int(request.form.get('amount'))
    
    if not user_id:
        return jsonify({'success': False, 'message': '사용자 ID가 필요합니다.'})
    
    ref = db.reference(f'users/{user_id}')
    user_data = ref.get()
    
    if not user_data:
        return jsonify({'success': False, 'message': '사용자를 찾을 수 없습니다.'})
    
    current_coins = user_data.get('coins', 0)
    if current_coins + amount < 0:
        return jsonify({'success': False, 'message': '코인이 부족합니다.'})
    
    user_data['coins'] = current_coins + amount
    ref.update({'coins': user_data['coins']})
    
    return jsonify({'success': True, 'coins': user_data['coins']})

# 🔹 메인2 페이지
@app.route("/main2")
def main2():
    user_id = request.args.get('user_id', '')
    # Firebase에서 사용자 정보 가져오기
    ref = db.reference('users')
    user_data = ref.child(user_id).get()
    
    if not user_data:
        # 새 사용자인 경우 기본 데이터 설정
        user_data = {
            'coins': 100,  # 초기 코인
            'level': 1,    # 초기 레벨
            'exp': 0,      # 초기 경험치
            'achievements': [],  # 업적 목록
            'daily_check': False  # 일일 출석 체크
        }
        ref.child(user_id).set(user_data)
    
    return render_template("main2.html", user_id=user_id, user_data=user_data)

# 🔹 일일 체크인
@app.route('/daily_check', methods=['POST'])
def daily_check():
    user_id = request.form.get('user_id')
    ref = db.reference(f'users/{user_id}')
    user_data = ref.get()
    
    if not user_data['daily_check']:
        # 코인과 경험치 보상
        user_data['coins'] += 50
        user_data['exp'] += 20
        user_data['daily_check'] = True
        
        # 레벨업 체크
        if user_data['exp'] >= user_data['level'] * 100:
            user_data['level'] += 1
            user_data['exp'] = 0
        
        ref.update(user_data)
        return jsonify({'success': True, 'coins': user_data['coins'], 'exp': user_data['exp'], 'level': user_data['level']})
    
    return jsonify({'success': False, 'message': '이미 오늘의 출석체크를 완료했습니다.'})

# 🔹 코인 사용/획득
@app.route('/update_coins', methods=['POST'])
def update_coins():
    user_id = request.form.get('user_id')
    amount = int(request.form.get('amount'))
    
    ref = db.reference(f'users/{user_id}')
    user_data = ref.get()
    
    if user_data['coins'] + amount >= 0:
        user_data['coins'] += amount
        ref.update({'coins': user_data['coins']})
        return jsonify({'success': True, 'coins': user_data['coins']})
    
    return jsonify({'success': False, 'message': '코인이 부족합니다.'})

# 🔹 추천 기록 페이지
@app.route("/records")
def records():
    try:
        ref = db.reference('recommendations')
        all_recommendations = ref.get()
        
        # 추천 기록이 없는 경우 빈 목록으로 처리
        if not all_recommendations:
            all_recommendations = {}
            
        return render_template("test2.html", recommendations=all_recommendations)
    except Exception as e:
        print(f"Error fetching records: {e}")
        return render_template("test2.html", recommendations={})

# 🔹 메인2 페이지
@app.route("/main2")
def main2():
    return render_template("main2.html")

# 🔹 기록 저장
@app.route("/save_record", methods=["POST"])
def save_record():
    try:
        # 요청 데이터 로깅
        content_type = request.headers.get('Content-Type')
        app.logger.info(f"Content-Type: {content_type}")
        
        if not request.is_json:
            app.logger.error("Content-Type이 application/json이 아닙니다.")
            return jsonify({"success": False, "error": "Content-Type must be application/json"}), 400
        
        try:
            data = request.get_json()
            app.logger.info(f"받은 데이터: {data}")
        except Exception as e:
            app.logger.error(f"JSON 파싱 오류: {e}")
            return jsonify({"success": False, "error": "잘못된 JSON 형식입니다."}), 400
        
        if not data:
            app.logger.error("빈 데이터 수신")
            return jsonify({"success": False, "error": "데이터가 비어있습니다."}), 400
        
        feeling = data.get("feeling")
        recommendations = data.get("recommendations")
        
        app.logger.info(f"감정: {feeling}")
        app.logger.info(f"추천곡: {recommendations}")
        
        if not feeling:
            app.logger.error("감정 데이터 누락")
            return jsonify({"success": False, "error": "감정 상태가 누락되었습니다."}), 400
            
        if not recommendations:
            app.logger.error("추천곡 데이터 누락")
            return jsonify({"success": False, "error": "추천곡 목록이 누락되었습니다."}), 400
        
        if not isinstance(recommendations, list):
            app.logger.error(f"잘못된 추천곡 형식: {type(recommendations)}")
            return jsonify({"success": False, "error": "recommendations는 리스트 형식이어야 합니다."}), 400
        
        # Firebase에 기록 저장
        try:
            records_ref = db.reference("records")
            new_record = {
                "feeling": feeling,
                "recommendations": recommendations,
                "timestamp": {".sv": "timestamp"}  # 서버 타임스탬프 사용
            }
            records_ref.push().set(new_record)
            app.logger.info("Firebase 저장 성공")
            return jsonify({"success": True})
        except Exception as e:
            app.logger.error(f"Firebase 저장 오류: {e}")
            return jsonify({"success": False, "error": f"데이터베이스 저장 중 오류: {str(e)}"}), 500
            
    except Exception as e:
        app.logger.error(f"기록 저장 중 예상치 못한 오류 발생: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# 🔹 기록 보기 페이지
@app.route("/records")
def view_records():
    try:
        # Firebase에서 기록 가져오기
        records_ref = db.reference("records")
        records = records_ref.get()
        
        # 기록이 없는 경우 빈 리스트로 처리
        if not records:
            records = []
        else:
            # 딕셔너리를 리스트로 변환하고 timestamp로 정렬
            processed_records = []
            for key, record in records.items():
                if isinstance(record, dict):
                    record_copy = record.copy()
                    record_copy['id'] = key
                    # timestamp가 있고 숫자인지 확인
                    if 'timestamp' in record_copy and isinstance(record_copy['timestamp'], (int, float)):
                        processed_records.append(record_copy)
                    else:
                        # timestamp가 없거나 잘못된 형식이면 현재 시간으로 설정
                        from time import time
                        record_copy['timestamp'] = int(time() * 1000)
                        processed_records.append(record_copy)
            
            # timestamp로 정렬
            records = sorted(processed_records, 
                           key=lambda x: x.get('timestamp', 0), 
                           reverse=True)
        
        app.logger.info(f"처리된 레코드: {records}")  # 디버깅을 위한 로그
        return render_template("records.html", records=records)
    except Exception as e:
        app.logger.error(f"기록 조회 중 오류 발생: {e}")
        return render_template("records.html", error=str(e), records=[])


# 🔹 로그인 페이지
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        user_id = request.form.get("id", "").strip()
        password = request.form.get("password", "").strip()

        if not user_id or not password:
            error = "아이디와 비밀번호를 모두 입력하세요."
            return render_template("login.html", error=error)

        # Firebase에서 유저 확인
        ref = db.reference(f"users/{user_id}")
        user = ref.get()

        if user and user.get("password") == password:
            return render_template("main2.html", user_id=user_id)
        else:
            error = "아이디 또는 비밀번호가 잘못되었습니다."

    return render_template("login.html", error=error)


# 🔹 회원가입 페이지
@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = None
    if request.method == "POST":
        user_id = request.form.get("id", "").strip()
        password = request.form.get("password", "").strip()

        if not user_id or not password:
            error = "아이디와 비밀번호를 모두 입력하세요."
            return render_template("signup.html", error=error)

        ref = db.reference(f"users/{user_id}")
        if ref.get():
            error = "이미 존재하는 아이디입니다."
        else:
            ref.set({
                "id": user_id,
                "password": password
            })
            return redirect(url_for("login"))

    return render_template("signup.html", error=error)


# 🔹 추천 페이지
@app.route("/recommend")
def recommend():
    return render_template("recommend.html")


# 🔹 설문조사 페이지
@app.route("/survey")
def survey():
    return render_template("survey.html")

import time

import re

def clean_recommendations(raw_text):
    lines = raw_text.splitlines()
    cleaned = []
    for line in lines:
        # 예: "1. 밤편지 - 아이유" → "밤편지 - 아이유"
        match = re.match(r'^\s*\d+\.\s*(.*)', line)
        if match:
            line = match.group(1)
        cleaned.append(line.strip())
    return '\n'.join(cleaned)


@app.route("/test2", methods=["GET", "POST"])
def test2():
    recommendations = None
    mood = None
    genre = None
    activity = None
    
    if request.method == "POST":
        try:
            mood = request.form.get("mood", "알 수 없음").strip()
            genre = request.form.get("genre", "").strip()
            activity = request.form.get("activity", "").strip()

            prompt = f"""
사용자의 설문 응답:
- 기분: {mood}
- 장르 선호: {genre}
- 현재 활동: {activity}

위 정보를 바탕으로 지금 듣기 좋은 노래 3곡을 한국어로 추천해줘.
형식은 아래처럼 숫자 없이 간단히:
곡명 - 가수
"""

            start_time = time.time()
            response = client.models.generate_content(
                model="gemini-2.5-flash", 
                contents=prompt
            )

            if time.time() - start_time > 20:
                app.logger.warning("API 응답 시간 초과")
                recommendations = "시간 초과로 인해 추천을 받을 수 없습니다."
            else:
                raw_recommendations = response.text if response else ""
                if raw_recommendations:
                    recommendations = clean_recommendations(raw_recommendations)
                    app.logger.info(f"생성된 추천: {recommendations}")
                else:
                    recommendations = "추천을 받을 수 없습니다."
                    app.logger.warning("API 응답이 비어있음")

        except Exception as e:
            app.logger.error(f"추천 생성 중 오류: {str(e)}")
            recommendations = "오류가 발생했습니다. 다시 시도해주세요."
    
    try:
        return render_template(
            "test2.html",
            mood=mood or "알 수 없음",
            genre=genre or "",
            activity=activity or "",
            recommendations=recommendations or ""
        )
    except Exception as e:
        app.logger.error(f"템플릿 렌더링 오류: {str(e)}")
        return "페이지를 표시하는 중 오류가 발생했습니다.", 500

@app.get("/api/youtube/search")
def youtube_search():
    title = request.args.get("title", "").strip()
    artist = request.args.get("artist", "").strip()
    if not title or not artist:
        return jsonify({"error": "title, artist 쿼리가 필요합니다."}), 400

    from dotenv import load_dotenv
    load_dotenv()
    YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
    if not YOUTUBE_API_KEY:
        return jsonify({"error": "YOUTUBE_API_KEY가 설정되지 않았습니다. .env에 넣고 앱을 재실행하세요."}), 500

    q = f'"{title}" "{artist}"'
    params = {
        "part": "snippet",
        "type": "video",
        "maxResults": 5,
        "order": "viewCount",
        "videoEmbeddable": "true",
        "relevanceLanguage": "ko",
        "regionCode": "KR",
        "q": q,
        "key": YOUTUBE_API_KEY,
        "fields": "items(id/videoId,snippet/title,snippet/channelTitle)"
    }

    try:
        r = requests.get("https://www.googleapis.com/youtube/v3/search",
                         params=params, timeout=10)
        if r.status_code != 200:
            # Google이 주는 에러 메시지 그대로 전달
            try:
                detail = r.json().get("error", {}).get("message", r.text)
            except Exception:
                detail = r.text
            return jsonify({"error": "YouTube API error", "detail": detail}), r.status_code

        data = r.json()
        items = data.get("items", [])
        if not items:
            return jsonify({"error": "검색 결과가 없습니다."}), 404

        la = artist.lower()
        for it in items:
            t = it["snippet"]["title"].lower()
            ch = it["snippet"]["channelTitle"].lower()
            if "official" in t or la in ch:
                return jsonify({"videoId": it["id"]["videoId"]})
        return jsonify({"videoId": items[0]["id"]["videoId"]})

    except requests.exceptions.RequestException as e:
        app.logger.exception("Upstream request failed")
        return jsonify({"error": "Upstream request failed", "detail": str(e)}), 502
    except Exception as e:
        app.logger.exception("Unhandled server error")
        return jsonify({"error": "Server error", "detail": str(e)}), 500

def get_youtube_link(title, artist):
    YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
    q = f'{title} {artist}'  # 따옴표 제거
    params = {
        "part": "snippet",
        "type": "video",
        "maxResults": 5,          # 결과 더 많이
        "q": q,
        "key": YOUTUBE_API_KEY,
        # "videoEmbeddable": "true",  # 제거
        # "regionCode": "KR",          # 제거
        "fields": "items(id/videoId)"
    }
    try:
        r = requests.get("https://www.googleapis.com/youtube/v3/search",
                         params=params, timeout=10)
        data = r.json()
        items = data.get("items", [])
        if items:
            vid = items[0]["id"]["videoId"]
            return f"https://www.youtube.com/watch?v={vid}"
        else:
            print("검색 결과 없음:", title, artist)
    except Exception as e:
        print("YouTube API 오류:", e)
    return None


if __name__ == "__main__":
    app.run(debug=True)
