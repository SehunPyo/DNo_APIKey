from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key')  # 세션용

# 메모리상 키 저장 (나중에 파일이나 DB로 교체 가능)
allowed_keys = set()

# 관리자 비밀번호 (환경변수로 관리)
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin1234')

# 관리자 로그인 페이지
@app.route('/admin/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        pw = request.form.get('password')
        if pw == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('manage_keys'))
        else:
            return "비밀번호가 틀렸습니다."
    return render_template_string("""
        <form method="post">
            비밀번호: <input type="password" name="password">
            <input type="submit" value="로그인">
        </form>
    """)

# 키 관리 페이지
@app.route('/admin/keys', methods=['GET'])
def manage_keys():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    keys_list = "<br>".join(f"{k} <a href='/admin/delete_key?key={k}'>[삭제]</a>" for k in allowed_keys)
    return render_template_string(f"""
        <h2>등록된 키 목록</h2>
        {keys_list}
        <hr>
        <form action="/admin/add_key" method="post">
            새 키 추가: <input name="key">
            <input type="submit" value="추가">
        </form>
        <br><a href="/admin/logout">로그아웃</a>
    """)

# 키 추가
@app.route('/admin/add_key', methods=['POST'])
def add_key():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    key = request.form.get('key')
    if key:
        allowed_keys.add(key)
    return redirect(url_for('manage_keys'))

# 키 삭제
@app.route('/admin/delete_key', methods=['GET'])
def delete_key():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    key = request.args.get('key')
    if key:
        allowed_keys.discard(key)
    return redirect(url_for('manage_keys'))

# 로그아웃
@app.route('/admin/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# 프로그램이 요청할 키 인증 API
@app.route('/validate', methods=['POST'])
def validate():
    data = request.json
    key = data.get('api_key')
    return jsonify({'allowed': key in allowed_keys})

# 홈 (기본 리다이렉트)
@app.route('/')
def index():
    return redirect('/admin/login')
