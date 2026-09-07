from flask import Flask, request
from random import choice

app = Flask(__name__)

app.json.ensure_ascii = False

about_me = {
   "name": "Михаил",
   "surname": "Шарапов",
   "email": "unreal-nv@yandex.ru"
}

quotes = [
   {
       "id": 3,
       "author": "Rick Cook",
       "text": "Программирование сегодня — это гонка разработчиков программ, стремящихся писать программы с большей и лучшей идиотоустойчивостью, и вселенной, которая пытается создать больше отборных идиотов. Пока вселенная побеждает."
   },
   {
       "id": 5,
       "author": "Waldi Ravens",
       "text": "Программирование на С похоже на быстрые танцы на только что отполированном полу людей с острыми бритвами в руках."
   },
   {
       "id": 6,
       "author": "Mosher’s Law of Software Engineering",
       "text": "Не волнуйтесь, если что-то не работает. Если бы всё работало, вас бы уволили."
   },
   {
       "id": 8,
       "author": "Yoggi Berra",
       "text": "В теории, теория и практика неразделимы. На практике это не так."
   },

]


def new_quote_id():
   return quotes[len(quotes)-1]["id"] + 1 if len(quotes) > 0 else 0

def find_quote(quote_id):
   for item in quotes:
      if item["id"] == quote_id:
         return item

@app.route("/")
def hello_world():
   return "Hello, World!"


@app.route("/about")
def about():
   return about_me


@app.route("/quotes")
def quotes_list():
   return quotes


@app.route("/quotes/<int:quote_id>")
def quote_by_id(quote_id):
   quote = find_quote(quote_id)
   if quote:
      return quote
   else:
      return f"Цитата с id={quote_id} не найдена", 404


@app.route("/quotes/count")
def quotes_count():
   return {"count": len(quotes)}


@app.route("/quotes/random")
def random_quote():
   return choice(quotes)
   

@app.route("/quotes", methods=['POST'])
def create_quote():
   data = request.json
   new_quote = data.copy()
   new_quote["id"] = new_quote_id()
   quotes.append(new_quote)
   return new_quote, 201


@app.route("/quotes/<int:quote_id>", methods=["PUT"])
def edit_qoute(quote_id):
   data = request.json
   quote = find_quote(quote_id)
   if quote:
      quote["author"] = data["author"]
      quote["text"] = data["text"]
      return quote, 200
   else:
      return f"Цитата с id={quote_id} не найдена для изменения", 404


@app.route("/quotes/<int:quote_id>", methods=["DELETE"])
def delete_quote(quote_id):
   quote = find_quote(quote_id)
   if quote:
      quotes.remove(quote)
      return f"Цитата с id={quote_id} успешно удалена", 200
   else:
      return f"Цитата с id={quote_id} не найдена для удаления", 404


if __name__ == "__main__":
   app.run(debug=True)