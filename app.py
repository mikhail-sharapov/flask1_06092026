from flask import Flask

app = Flask(__name__)


@app.route("/") # Это первый URL, который будем обрабатывать
def hello_world(): # Это функция обработчик, которая будет вызвана при запросе URL
   return "Hello, World!"


if __name__ == "__main__":
   app.run(debug=True)