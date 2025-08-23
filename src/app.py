from flask import Flask, render_template, request, redirect, url_for
import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, db
from google import genai
# import google.generativeai as genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# client = genai.Client()
client = genai.Client(api_key=GEMINI_API_KEY)
# 🔹 Gemini API 초기화

# Flask 초기화
app = Flask(__name__)

# 🔹 .env 불러오기
load_dotenv()
# genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# 🔹 Firebase 연결
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # src 폴더 경로
cred_path = os.path.join(BASE_DIR, "firebase_key.json")  # 무조건 app.py와 같은 폴더에서 찾음
db_url = os.getenv("FIREBASE_DB_URL")

# 키 파일 & DB URL 체크
if not os.path.exists(cred_path):
    raise FileNotFoundError(f"❌ Firebase 키 파일을 찾을 수 없습니다: {cred_path}")

if not db_url:
    raise ValueError("❌ 환경변수 FIREBASE_DB_URL이 설정되지 않았습니다. .env 파일을 확인하세요.")

# Firebase 초기화 (중복 방지)
if not firebase_admin._apps:
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred, {
        "databaseURL": db_url
    })


# 🔹 메인 페이지
@app.route("/")
def index():
    return render_template("main.html")


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
            return render_template("main2.html", user_id=user_id)  # 로그인 성공
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


# 🔹 설문 제출 후 GPT 추천
@app.route("/test2", methods=["GET", "POST"])
def test2():
    if request.method == "POST":
        mood = request.form.get("mood")
        genre = request.form.get("genre")
        activity = request.form.get("activity")

        # Gemini API 요청
        # model = genai.GenerativeModel("gemini-pro")
        prompt = f"""
        사용자의 설문 응답:
        - 기분: {mood}
        - 장르 선호: {genre}
        - 현재 활동: {activity}

        위 정보를 바탕으로 지금 듣기 좋은 노래 3곡을 한국어로 추천해줘.
        (곡명 - 가수 형식으로 간단히)
        """

        #response = model.generate_content(prompt)
        #recommendations = response.text if response else "추천 결과를 가져오지 못했습니다."
        recommendations = client.models.generate_content(model = "gemini-2.5-flash", contents = prompt)
        # 결과 페이지에 전달
        print(f"recommendations: {recommendations}")
        result_text = recommendations.candidates[0].content.parts[0].text
        return render_template("test2.html",
                               mood=mood,
                               genre=genre,
                               activity=activity,
                               recommendations=result_text)

    return render_template("test2.html", recommendations=None)
    

if __name__ == "__main__":
    app.run(debug=True)
