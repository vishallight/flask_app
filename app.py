from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return 'Hello, Welcome to My Flask App! First,3 external Change'

if __name__ == '__main__':
    app.run(debug=True)
