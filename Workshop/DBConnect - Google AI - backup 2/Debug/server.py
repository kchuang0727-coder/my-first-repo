import os
from flask import Flask, jsonify
from cfenv import AppEnv
from hdbcli import dbapi

app = Flask(__name__)

env = AppEnv()

def get_hana_connection():

    hana_service = env.get_service(name_filter=".*hana.*")
    
    if not hana_service:
        raise Exception("找不到綁定的 HANA Cloud 服務實例，請確認 Binding 是否成功建立。")
        
    creds = hana_service.credentials
    
    conn = dbapi.connect(
        address=creds.get("host"),
        port=int(creds.get("port")),
        user=creds.get("user"),
        password=creds.get("password")
    )
    return conn

@app.route('/')
def hello_world():
    return "Hello World! This is a Python app running on SAP BTP."

@app.route('/hana-info')
def get_hana_info():
    conn = None
    try:
        conn = get_hana_connection()
        cursor = conn.cursor()
        
        sql_query = "SELECT VERSION, CURRENT_USER, CURRENT_TIMESTAMP FROM SYS.M_DATABASE"
        cursor.execute(sql_query)
        row = cursor.fetchone()
        
        cursor.close()
        
        return jsonify({
            "status": "Success",
            "message": "Successfully connected to SAP HANA Cloud!",
            "database_version": row[0],
            "connected_as_user": row[1],
            "hana_system_time": row[2]
        })
        
    except Exception as e:
        return jsonify({
            "status": "Failed",
            "error_message": str(e)
        }), 500
        
    finally:
        if conn and conn.isconnected():
            conn.close()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
