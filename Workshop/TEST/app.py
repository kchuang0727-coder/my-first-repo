import os
from flask import Flask, render_template_string
from cfenv import AppEnv
from hdbcli import dbapi

app = Flask(__name__)
env = AppEnv()

def get_hana_connection():
    """自動取得 HDI Container 連線資訊"""
    hana_service = env.get_service(label='hana') or env.get_service(label='hanatrial')
    if not hana_service:
        raise ConnectionError("找不到綁定的 HDI Container 服務，請確認 Service Binding。")
    creds = hana_service.credentials
    return dbapi.connect(
        address=creds.get('host'),
        port=int(creds.get('port')),
        user=creds.get('user'),
        password=creds.get('password'),
        encrypt='true',
        sslValidateCertificate='false'
    )

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>SAP BTP Python HANA Demo</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; background-color: #f4f6f9; color: #333; }
        .card { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); max-width: 800px; margin: 0 auto 20px auto; }
        h2 { color: #1d2d50; border-bottom: 2px solid #eee; padding-bottom: 10px; margin-top: 0; }
        h3 { color: #0070f2; margin-top: 25px; }
        .status { padding: 10px 15px; border-radius: 4px; font-weight: bold; display: inline-block; margin-bottom: 20px; }
        .success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .failed { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; margin-bottom: 20px; }
        th, td { text-align: left; padding: 12px; border-bottom: 1px solid #ddd; }
        th { background-color: #f8f9fa; color: #555; }
        .sql-box { background-color: #272822; color: #f8f8f2; padding: 12px; border-radius: 4px; font-family: monospace; font-size: 14px; margin-bottom: 15px; }
        .footer { text-align: center; margin-top: 20px; font-size: 12px; color: #777; }
    </style>
</head>
<body>
    <div class="card">
        <h2>📊 SAP BTP 應用程式連線狀態</h2>
        
        {% if is_success %}
            <div class="status success">🟢 連線成功 (Connected)</div>
            
            <h3>📌 系統基本資訊 (M_DATABASE)</h3>
            <table>
                <tr><th style="width: 30%;">項目</th><th>資料庫回傳結果</th></tr>
                <tr><td><b>HANA 系統時間</b></td><td>{{ time }}</td></tr>
                <tr><td><b>HANA 版本資訊</b></td><td>{{ version }}</td></tr>
            </table>

            <h3>🔍 自訂 SQL 執行結果</h3>
            <!-- 👈 修正顯示的 SQL 語法 -->
            <div class="sql-box">SELECT USER_NAME, USER_MODE, CREATE_TIME FROM SYS.USERS LIMIT 5;</div>
            
            <table>
                <thead>
                    <tr>
                        <th>使用者名稱 (USER_NAME)</th>
                        <th>模式 (USER_MODE)</th>
                        <th>建立時間 (CREATE_TIME)</th>
                    </tr>
                </thead>
                <tbody>
                    {% for row in sql_rows %}
                    <tr>
                        <!-- 👈 修正前端陣列索引, [1], [2] 對應欄位 -->
                        <td><span style="color: #0070f2; font-weight: bold;">{{ row[0] }}</span></td>
                        <td>{{ row[1] }}</td>
                        <td>{{ row[2] }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            
        {% else %}
            <div class="status failed">🔴 連線失敗 (Failed)</div>
            <p style="color: #721c24;"><b>錯誤原因：</b><br>{{ error }}</p>
        {% endif %}
    </div>
    <div class="footer">環境：SAP BTP Cloud Foundry | 驅動：hdbcli</div>
</body>
</html>
"""

@app.route('/')
def index():
    try:
        conn = get_hana_connection()
        cursor = conn.cursor()
        
        # SQL 1: 查詢系統時間
        cursor.execute("SELECT CURRENT_TIMESTAMP, VERSION FROM M_DATABASE")
        db_info = cursor.fetchone()
        
        # SQL 2: 修正為 CREATE_TIME
        cursor.execute("SELECT USER_NAME, USER_MODE, CREATE_TIME FROM SYS.USERS LIMIT 5")
        sql_rows = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template_string(
            HTML_TEMPLATE, 
            is_success=True, 
            time=str(db_info[0]), # 僅取出時間字串 
            version=db_info[1],    # 僅取出版本字串
            sql_rows=sql_rows
        )
    except Exception as e:
        return render_template_string(
            HTML_TEMPLATE, 
            is_success=False, 
            error=str(e)
        )

port = int(os.environ.get("PORT", 8080))
app.run(host='0.0.0.0', port=port, threaded=True)
