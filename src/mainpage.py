from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('main.html')

@app.route('/login', methods=['POST'])
def login():
    valid_username = "user1"
    valid_password = "1234"
    username = request.form.get('username')
    password = request.form.get('password')

    if username == valid_username and password == valid_password:
        return f"<h2>로그인 성공! 환영합니다, {username}님.</h2>"
    else:
        return "<h2 style='color:red;'>아이디 또는 비밀번호가 틀렸습니다.</h2><a href='/'>돌아가기</a>"

if __name__ == '__main__':
    app.run(debug=True)
