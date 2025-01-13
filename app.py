from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return 'Hello, Next Change in VM FInal Check 2| v4 '

if __name__ == '__main__':
    app.run(host='0.0.0.0', port = 80, debug=True)
