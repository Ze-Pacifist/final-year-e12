from flask import Flask # type: ignore
app = Flask(__name__)

@app.route('/health')
def health():
    return "Python Challenge is running!"

@app.route('/')
def hello():
    print("hello python")
    return "Hello from Python Challenge!"

@app.route('/flag')
def flag():
    from flask import request
    with open('/tmp/flags', 'a') as f:
        f.write(request.args.get('flag', '') + '\n')
    return 'Flag submitted'


if __name__ == '__main__':
    print("running python app")
    app.run(host='0.0.0.0', port=5000)
