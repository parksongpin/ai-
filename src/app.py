from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# 샘플 사용자 데이터 (DB 대신 사용)
users = {}

# 메인 페이지
@app.route('/')
def main():
    return render_template('main.html')

# 로그인 페이지
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username] == password:
            flash('로그인 성공!', 'success')
            return redirect(url_for('main2'))  # 여기 수정: main2.html로 이동
        else:
            flash('아이디 또는 비밀번호가 잘못되었습니다.', 'error')
    return render_template('login.html')

# 회원가입 페이지
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if username in users:
            flash('이미 존재하는 아이디입니다.', 'error')
        elif password != confirm_password:
            flash('비밀번호가 일치하지 않습니다.', 'error')
        else:
            users[username] = password
            flash('회원가입 성공! 로그인 페이지로 이동합니다.', 'success')
            return redirect(url_for('login'))
    return render_template('signup.html')

# main2 페이지 라우트 추가
@app.route('/main2')
def main2():
    return render_template('main2.html')  # main2.html 파일 필요

if __name__ == '__main__':
    app.run(debug=True)
