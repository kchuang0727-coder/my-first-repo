import os 
from flask import Flask

app = Flask(__name__)

port = int(os.environ.get("PORT", 8080))

@app.route("/")
def hello():
	return "Hello from Python on SAP BTP Cloud Foundry!"

if __name__ == "__main__":
	app.run(host="0.0.0.0", port=port)