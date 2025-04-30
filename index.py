from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
from datetime import datetime
import os
import requests

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key')

# Supabase 환경 변수
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
SUPABASE_API_URL = f"{SUPABASE_URL}/rest/v1/api_keys"

# 관리자 비밀번호
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin1234')

# Supabase 공통 헤더
def supabase_headers():
    return {
        'apikey': SUPABASE_SERVICE_KEY,
        'Authorization': f"Bearer {SUPABASE_SERVICE_KEY}",
        'Content-Type': 'application/json'
    }

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

    try:
        params = {'order': 'created_at.desc'}
        if search_query:
            params['name'] = f'ilike.*{search_query}*'

        res = requests.get(SUPABASE_API_URL, headers=supabase_headers(), params=params)
        keys = res.json() if res.ok else []

    except Exception as e:
        return f"Supabase 연결 실패: {e}"

    keys_list_html = "".join(
        f"<tr><td>{item['name']}</td><td>{item['key']}</td><td>{item['created_at']}</td>"
        f"<td><a href='/admin/delete_key?name={item['name']}'>[삭제]</a></td></tr>"
        for item in keys
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
        try:
            payload = {
                "name": name,
                "key": key,
                "created_at": datetime.now().isoformat()
            }
            res = requests.post(SUPABASE_API_URL, headers=supabase_headers(), json=payload)
        except Exception as e:
            return f"Supabase 저장 실패: {e}"

    return redirect(url_for('manage_keys'))

@app.route('/admin/delete_key', methods=['GET'])
def delete_key():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    name = request.args.get('name')
    if name:
        try:
            res = requests.delete(SUPABASE_API_URL, headers=supabase_headers(), params={
                'name': f'eq.{name}'
            })
        except Exception as e:
            return f"Supabase 삭제 실패: {e}"

    return redirect(url_for('manage_keys'))

@app.route('/validate', methods=['POST'])
def validate():
    data = request.json
    key_to_check = data.get('api_key')
    try:
        response = requests.get(SUPABASE_API_URL, headers=supabase_headers(), params={
            'key': f'eq.{key_to_check}'
        })
        is_allowed = response.status_code == 200 and len(response.json()) > 0
        return jsonify({'allowed': is_allowed})
    except Exception as e:
        print("Supabase 연결 실패:", e)
        return jsonify({'allowed': False})

@app.route('/')
def index():
    return redirect('/admin/login')
