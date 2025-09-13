# app.py
from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS  # 프론트가 다른 도메인이면 필요
import os, requests
import dotenv

app = Flask(__name__, template_folder="templates")
CORS(app)

dotenv.load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
print(f"YOUTUBE_API_KEY: {YOUTUBE_API_KEY}")
@app.get("/")
def index():
    return render_template("index.html")

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

if __name__ == "__main__":
    app.run(debug=True)  # 배포 시 debug=False