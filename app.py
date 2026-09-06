from flask import Flask

app = Flask(__name__)

app.json.ensure_ascii = False

@app.route("/") # Это первый URL, который будем обрабатывать
def hello_world(): # Это функция обработчик, которая будет вызвана при запросе URL
   return "Hello, World!"

about_me = {
   "name": "Михаил",
   "surname": "Шарапов",
   "email": "unreal-nv@yandex.ru"
}

@app.route("/about")
def about():
   return about_me

if __name__ == "__main__":
   app.run(debug=True)