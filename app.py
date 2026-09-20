from flask import Flask, request, jsonify
from pathlib import Path

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String
from flask_migrate import Migrate

class Base(DeclarativeBase):
   pass

BASE_DIR = Path(__file__).parent

app = Flask(__name__)

app.config['JSON_AS_ASCII'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{BASE_DIR / 'quotes.db'}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(model_class=Base)
db.init_app(app)

migrate = Migrate(app, db)

class QuoteModel(db.Model):
   __tablename__ = 'quotes'

   id: Mapped[int] = mapped_column(primary_key=True)
   author: Mapped[str] = mapped_column(String(32))
   text: Mapped[str] = mapped_column(String(255))
   rating: Mapped[int]

   RATING_RANGE = range(1,6)
   DEFAULT_RATING = 1

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

   @staticmethod
   def validate_rating(rating):
      if rating not in QuoteModel.RATING_RANGE:
         return QuoteModel.DEFAULT_RATING
      return rating

   @classmethod
   def create_quote(cls, data: dict):
      fields = ("author", "text")
      values = [data.get(field) for field in fields]

      values.append(cls.validate_rating(data.get("rating")))

      if None in values:
         return None
      return cls(*values)

   def edit_quote(self, data: dict):
      self.author = data["author"] if data.get("author") else self.author
      self.text = data["text"] if data.get("text") else self.text
      self.rating = QuoteModel.validate_rating(data["rating"]) if data.get("rating") else self.rating


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
   

@app.route("/quotes", methods=['POST'])
def create_quote():
   data = request.json.copy()
   if not isinstance(data, list):
      data = [data]
   
   quotes = []
   for item in data:
      new_quote = QuoteModel.create_quote(item)
      if new_quote:
         quotes.append(new_quote)
   
   if len(quotes):
      db.session.add_all(quotes)
      db.session.commit()

   return jsonify(result=f"Добавлено цитат: {len(quotes)}"), 200


@app.route("/quotes/<int:quote_id>", methods=["PUT"])
def edit_qoute(quote_id):
   data = request.json.copy()

   quote = db.get_or_404(QuoteModel, quote_id, description=f"Не найдена цитата для редактирования с id={quote_id}")
   quote.edit_quote(data)
   db.session.commit()

   return quote.to_dict(), 200


@app.route("/quotes/<int:quote_id>", methods=["DELETE"])
def delete_quote(quote_id):
   quote = db.get_or_404(QuoteModel, quote_id, description=f"Не найдена цитата для удаления с id={quote_id}")
   db.session.delete(quote)
   db.session.commit()

   return jsonify(result=f"Цитата с id={quote_id} успешно удалена"), 200


@app.route("/quotes/filter")
def filter_quotes():
   args = {key: value for key, value in request.args.items() if key in ("author", "rating")}
   quotes = db.session.execute(db.select(QuoteModel).filter_by(**args)).scalars()
   return jsonify([item.to_dict() for item in quotes]), 200 


if __name__ == "__main__":
   app.run(debug=True)