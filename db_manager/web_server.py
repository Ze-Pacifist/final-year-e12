from flask import Flask, send_file
from flask_cors import CORS
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)


@app.route('/')
def serve_scoreboard():
    return send_file('scoreboard.html')

if __name__ == '__main__':
    app.run(port=int(os.getenv('WEB_PORT', 5001)))