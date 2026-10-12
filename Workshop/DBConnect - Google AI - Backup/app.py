import os
from flask import Flask, jsonify
from cfenv import AppEnv
from hdbcli import dbapi

app = Flask(__name__)
env = AppEnv()

def get_hana_connection():
    """從 BTP 綁定的 VCAP_SERVICES 中自動取得 HDI Container 連線資訊"""
    # 優先尋找標準的 hana (HDI-shared) 服務標籤
    hana_service = env.get_service(label='hana') or env.get_service(label='hanatrial')
    
    if not hana_service:
        raise ConnectionError("找不到綁定的 HDI Container 服務，請確認 Service Binding。")
        
    creds = hana_service.credentials
    
    # 建立資料庫連線
    return dbapi.connect(
        address=creds.get('host'),
        port=int(creds.get('port')),
        user=creds.get('user'),
        password=creds.get('password'),
        encrypt='true',
        sslValidateCertificate='false'
    )

@app.route('/')
def index():
    connection_status = "失敗"
    sql_result = []
    error_message = None

    try:
        conn = get_hana_connection()
        connection_status = "成功！已成功連線至同 Subaccount 的 HANA Cloud (hana_cloud_dev)。"
        
        cursor = conn.cursor()
        # 執行簡單 SQL
        cursor.execute("SELECT CURRENT_TIMESTAMP, VERSION FROM M_DATABASE")
        row = cursor.fetchone()
        
        if row:
            sql_result = {
                "HANA_Current_Time": str(row[0]),
                "HANA_Version": row[1]
            }
            
        cursor.close()
        conn.close()

    except Exception as e:
        connection_status = f"失敗。錯誤原因: {str(e)}"
        error_message = str(e)

    return jsonify({
        "Application_Status": "Running",
        "HANA_Connection_Result": connection_status,
        "SQL_Execution_Result": sql_result,
        "Error_Log": error_message
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
