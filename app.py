import sqlite3
from flask import Flask, request, jsonify, g
from random import choice
from pathlib import Path

BASE_DIR = Path(__file__).parent
path_to_db = BASE_DIR / "store.db"

app = Flask(__name__)

app.json.ensure_ascii = False


def get_db():
   db = getattr(g, "_database", None)
   if db is None:
      db = g._database = sqlite3.connect(path_to_db)

   def make_dict(cursor, row):
      return dict((cursor.description[idx][0], value) for idx, value in enumerate(row))
   
   db.row_factory = make_dict

   return db


@app.teardown_appcontext
def close_connection(exception):
   db = getattr(g, "_database", None)
   if db is not None:
      db.close()


def query_db(query, args=(), one=None):
   cursor = get_db().execute(query, args)
   if one:
      result = cursor.fetchone()
   else:
      result = cursor.fetchall()
   cursor.close()
   return result

# MAX_RATING = 5

# about_me = {
#    "name": "Михаил",
#    "surname": "Шарапов",
#    "email": "unreal-nv@yandex.ru"
# }

# quotes = [
#    {
#        "id": 3,
#        "author": "Rick Cook",
#        "text": "Программирование сегодня — это гонка разработчиков программ, стремящихся писать программы с большей и лучшей идиотоустойчивостью, и вселенной, которая пытается создать больше отборных идиотов. Пока вселенная побеждает.",
#        "rating": 1
#    },
#    {
#        "id": 5,
#        "author": "Waldi Ravens",
#        "text": "Программирование на С похоже на быстрые танцы на только что отполированном полу людей с острыми бритвами в руках.",
#        "rating": 2
#    },
#    {
#        "id": 6,
#        "author": "Mosher’s Law of Software Engineering",
#        "text": "Не волнуйтесь, если что-то не работает. Если бы всё работало, вас бы уволили.",
#        "rating": 2
#    },
#    {
#        "id": 8,
#        "author": "Yoggi Berra",
#        "text": "В теории, теория и практика неразделимы. На практике это не так.",
#        "rating": 3
#    },

# ]


@app.route("/quotes")
def quotes_list():
   query_text = "SELECT * from quotes"
   quotes_db = query_db(query_text)
   return jsonify(quotes_db), 200
   # cursor = get_db().cursor()
   # cursor.execute(select_quotes)
   # quotes_db = cursor.fetchall() # list[tuple]
   # cursor.close()
   # result = []
   # keys = ("id", "author", "text")
   # for item in quotes_db:
   #    quote = dict(zip(keys, item))
   #    result.append(quote)
   # return jsonify(result), 200


@app.route("/quotes/<int:quote_id>")
def quote_by_id(quote_id):
   query_text = "SELECT * from quotes WHERE id=?"
   quote = query_db(query_text, (str(quote_id),), True)
   if quote:
      return jsonify(quote), 200
   else:
      return jsonify(error=f"Цитата с id={quote_id} не найдена"), 404
   # connection = sqlite3.connect(path_to_db)
   # cursor = connection.cursor()
   # cursor.execute(select_quotes, (str(quote_id),))
   # quote = cursor.fetchone()
   # cursor.close()
   # connection.close()
   # if quote:
   #    keys = ("id", "author", "text")
   #    return jsonify(dict(zip(keys, quote))), 200
   # else:
   #    return jsonify(error=f"Цитата с id={quote_id} не найдена"), 404


# @app.route("/quotes/count")
# def quotes_count():
#    return {"count": len(quotes)}


# @app.route("/quotes/random")
# def random_quote():
#    return choice(quotes)
   

@app.route("/quotes", methods=['POST'])
def create_quote():
   data = request.json

   query_text = """
   INSERT INTO
   quotes (author,text)
   VALUES
   (?, ?);
   """

   if isinstance(data, list):
      query_param = [(item["author"], item["text"]) for item in data]
   else:
      query_param = [(data["author"], data["text"])]
   
   cursor = get_db().executemany(query_text, query_param)
   get_db().commit()
   cursor.close()

   return jsonify(result=f"Добавлено цитат - {len(query_param)}"), 200


@app.route("/quotes/<int:quote_id>", methods=["PUT"])
def edit_qoute(quote_id):
   data = request.json

   fields = [key+"=?" for key in data.keys()]
   values = tuple([value for value in data.values()])

   update_quotes = f"""
   UPDATE quotes 
   SET {", ".join(fields)}
   WHERE id={quote_id};
   """
   connection = sqlite3.connect(path_to_db)
   cursor = connection.cursor()
   cursor.execute(update_quotes, values)
   rowcount = cursor.rowcount
   connection.commit()
   cursor.close()
   connection.close()
   if rowcount:
      quote = data.copy()
      quote["id"] = quote_id
      return jsonify(quote), 200
   else:
      return jsonify(error=f"Цитата с id={quote_id} не найдена для изменения"), 404


@app.route("/quotes/<int:quote_id>", methods=["DELETE"])
def delete_quote(quote_id):
   delete_quotes = """
   DELETE FROM quotes WHERE id=?;
   """
   connection = sqlite3.connect(path_to_db)
   cursor = connection.cursor()
   cursor.execute(delete_quotes, (quote_id,))
   rowcount = cursor.rowcount
   connection.commit()
   cursor.close()
   connection.close()
   if rowcount:
      return jsonify(result=f"Цитата с id={quote_id} успешно удалена"), 200
   else:
      return jsonify(error=f"Цитата с id={quote_id} не найдена для удаления"), 404


# @app.route("/quotes/filter")
# def filter_quotes():
#    args = request.args
#    author = args.get("author")
#    rating = args.get("rating")
#    result = [item for item in quotes if (not author or item["author"] == author) and (not rating or item["rating"] == int(rating))]
#    return result

if __name__ == "__main__":
   app.run(debug=True)