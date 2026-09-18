import sqlite3
from typing import Any
from flask import Flask, request, jsonify, g, abort
from pathlib import Path

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String

class Base(DeclarativeBase):
   pass

BASE_DIR = Path(__file__).parent

app = Flask(__name__)

app.config['JSON_AS_ASCII'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{BASE_DIR / 'main.db'}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(model_class=Base)
db.init_app(app)

class QuoteModel(db.Model):
   __tablename__ = 'quotes'

   id: Mapped[int] = mapped_column(primary_key=True)
   author: Mapped[str] = mapped_column(String(32))
   text: Mapped[str] = mapped_column(String(255))
   rating: Mapped[int]

   RATING_RANGE = range(1,6)

   def __init__(self, author, text, rating):
      self.author = author
      self.text  = text
      self.rating = rating

   def to_dict(self):
      return {
         "id": self.id,
         "author": self.author,
         "text": self.text,
         "rating": self.rating
      }

   @classmethod
   def create_quote(cls, data: dict):
      fields = set("author", "text")
      # if set(data.keys()) & fields == fields:



@app.errorhandler(404)
def error_handler(error):
   return jsonify(message = error.description), 404


@app.route("/quotes")
def quotes_list():
   quotes_db = db.session.scalars(db.select(QuoteModel)).all()
   return jsonify([item.to_dict() for item in quotes_db]), 200


@app.route("/quotes/<int:quote_id>")
def quote_by_id(quote_id):
   quote_db = db.get_or_404(QuoteModel, quote_id, description=f"Не найдена цитата с id={quote_id}")
   return quote_db.to_dict(), 200
   # quote_db = db.session.get(QuoteModel, quote_id)
   # if quote_db:
   #    return quote_db.to_dict(), 200
   # else:
   #    abort(404, f"Не найдена цитата с id={quote_id}")
   

@app.route("/quotes", methods=['POST'])
def create_quote():
   data = request.json.copy()
   if not isinstance(data, list):
      data = [data]
   
   new_quotes = [QuoteModel(item["author"], item["text"], item.get("rating")) for item in data]
   for item in new_quotes:
      db.session.add(item)
   db.session.commit()

   return jsonify(result=f"Добавлено цитат: {len(new_quotes)}"), 200

   # query_text = """
   # INSERT INTO
   # quotes (author,text)
   # VALUES
   # (?, ?);
   # """

   # if isinstance(data, list):
   #    query_param = [(item["author"], item["text"]) for item in data]
   # else:
   #    query_param = [(data["author"], data["text"])]
   
   # cursor = get_db().executemany(query_text, query_param)
   # get_db().commit()
   # cursor.close()

   # return jsonify(result=f"Добавлено цитат: {len(query_param)}"), 200


@app.route("/quotes/<int:quote_id>", methods=["PUT"])
def edit_qoute(quote_id):
   data = request.json

   fields = [key+"=?" for key in data.keys()]
   values = [value for value in data.values()]

   query_text = f"""
   UPDATE quotes 
   SET {", ".join(fields)}
   WHERE id=?
   RETURNING id, author, text;
   """

   cursor = get_db().execute(query_text, (*values, quote_id))
   quote = cursor.fetchone()
   get_db().commit()
   cursor.close()

   if cursor.rowcount:      
      return jsonify(quote), 200
   else:
      return jsonify(error=f"Цитата с id={quote_id} не найдена для изменения"), 404


@app.route("/quotes/<int:quote_id>", methods=["DELETE"])
def delete_quote(quote_id):
   query_text = "DELETE FROM quotes WHERE id=?;"

   cursor = get_db().execute(query_text, (quote_id,))
   get_db().commit()
   rowcount = cursor.rowcount
   cursor.close()

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