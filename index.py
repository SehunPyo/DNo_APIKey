from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session, request
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key')

# 메모리상 키 저장 (name: (key, 등록일) 구조)
allowed_keys = {}

# 관리자 비밀번호
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin1234')

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

@app.route('/admin/keys', methods=['GET', 'POST'])
def manage_keys():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    search_query = request.form.get('search', '').strip()

    # 이름 필터링
    filtered_keys = {
        name: (key, reg_date)
        for name, (key, reg_date) in allowed_keys.items()
        if search_query.lower() in name.lower()
    } if search_query else allowed_keys

    # 등록일 기준 정렬 (최신순)
    sorted_keys = sorted(
        filtered_keys.items(),
        key=lambda item: item[1][1],  # 등록일 기준
        reverse=True
    )

    keys_list_html = "".join(
        f"<tr><td>{name}</td><td>{key}</td><td>{reg_date}</td><td><a href='/admin/delete_key?name={name}'>[삭제]</a></td></tr>"
        for name, (key, reg_date) in sorted_keys
    )

    return render_template_string(f"""
        <html>
        <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }}
            th, td {{
                padding: 12px;
                text-align: center;
                border-bottom: 1px solid #ddd;
            }}
            th {{
                background-color: #f4f6f8;
            }}
            tr:hover {{
                background-color: #f1f1f1;
            }}
            form {{
                margin-bottom: 20px;
            }}
            input[type="text"] {{
                padding: 8px;
                margin-right: 5px;
            }}
            input[type="submit"] {{
                padding: 8px 12px;
                background-color: #4CAF50;
                color: white;
                border: none;
                cursor: pointer;
                border-radius: 5px;
            }}
            input[type="submit"]:hover {{
                background-color: #45a049;
            }}
            a {{
                color: #d9534f;
                text-decoration: none;
            }}
            a:hover {{
                text-decoration: underline;
            }}
        </style>
        </head>
        <body>
            <h2>등록된 키 목록</h2>
            <form action="/admin/add_key" method="post">
                이름: <input type="text" name="name" required>
                키: <input type="text" name="key" required>
                <input type="submit" value="추가">
            </form>
            <form action="/admin/keys" method="post">
                이름 검색: <input type="text" name="search" value="{search_query}">
                <input type="submit" value="검색">
            </form>
            <table>
                <thead>
                    <tr>
                        <th>이름</th><th>API Key</th><th>등록일</th><th>삭제</th>
                    </tr>
                </thead>
                <tbody>
                    {keys_list_html}
                </tbody>
            </table>
            <br><a href="/admin/logout">로그아웃</a>
        </body>
        </html>
    """)

@app.route('/admin/add_key', methods=['POST'])
def add_key():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    name = request.form.get('name')
    key = request.form.get('key')
    if name and key:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        allowed_keys[name] = (key, now)
    return redirect(url_for('manage_keys'))

@app.route('/admin/delete_key', methods=['GET'])
def delete_key():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    name = request.args.get('name')
    if name:
        allowed_keys.pop(name, None)
    return redirect(url_for('manage_keys'))

@app.route('/validate', methods=['POST'])
def validate():
    data = request.json
    key = data.get('api_key')
    return jsonify({'allowed': key in [k for k, _ in allowed_keys.values()]})

@app.route('/')
def index():
    return redirect('/admin/login')
