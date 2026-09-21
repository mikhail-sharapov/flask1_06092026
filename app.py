import datetime
from flask import Flask, request, jsonify, abort
from pathlib import Path

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, func, ForeignKey, Integer, Boolean, DateTime
from flask_migrate import Migrate
from http import HTTPStatus

class Base(DeclarativeBase):
   pass

BASE_DIR = Path(__file__).parent

app = Flask(__name__)

app.json.ensure_ascii = False

app.config['JSON_AS_ASCII'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{BASE_DIR / 'quotes.db'}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["SQLALCHEMY_ECHO"] = True

db = SQLAlchemy(model_class=Base)
db.init_app(app)

migrate = Migrate(app, db)

class AuthorModel(db.Model):
   __tablename__ = 'authors'
   id: Mapped[int] = mapped_column(primary_key=True)
   name: Mapped[int] = mapped_column(String(32), index= True, unique=True)
   surname: Mapped[str] = mapped_column(String(32), index= True, server_default='undefined')
   quotes: Mapped[list['QuoteModel']] = relationship( back_populates='author', lazy='dynamic', cascade="all, delete-orphan")
   is_deleted: Mapped[bool] = mapped_column(Boolean, server_default='0', default='0', nullable=False)

   def __init__(self, name, surname):
      self.name = name
      self.surname = surname
      self.is_deleted=False

   def to_dict(self):
      return {
         "id": self.id,
         "name": self.name,
         "surname": self.surname,
      }

class QuoteModel(db.Model):
   __tablename__ = 'quotes'

   id: Mapped[int] = mapped_column(primary_key=True)
   author_id: Mapped[str] = mapped_column(ForeignKey('authors.id'))
   author: Mapped['AuthorModel'] = relationship(back_populates='quotes')
   text: Mapped[str] = mapped_column(String(255))
   rating: Mapped[int] = mapped_column(Integer, nullable=False, server_default='1', default='1')
   created: Mapped[datetime.datetime] = mapped_column(DateTime(), server_default=func.now())

   def __init__(self, author, text):
      self.author = author
      self.text  = text

   RATING_RANGE = range(1,6)

   def __init__(self, author, text, rating):
      self.author = author
      self.text  = text
      self.rating = QuoteModel.validate_rating(rating)

   def to_dict(self):
      return {
         "id": self.id,
         "author": f"{self.author.name} {self.author.surname}",
         "text": self.text,
         "rating": self.rating,
         "created": self.created.strftime("%d.%m.%Y"),
      }

   @staticmethod
   def validate_rating(rating, default=1):
      if rating not in QuoteModel.RATING_RANGE:
         return default
      return rating
   
   def edit_rating(self, operation):
      self.rating = QuoteModel.validate_rating(operation(self.rating), default=self.rating)


@app.errorhandler(404)
def error_handler(error):
   return jsonify(message = error.description), 404


"""Authors"""

@app.route("/authors")
def authors_list():
   """Получение всех авторов"""
   authors_db = db.session.scalars(db.select(AuthorModel).where(AuthorModel.is_deleted==False)).all()
   return jsonify([item.to_dict() for item in authors_db]), 200


@app.route("/authors/<int:author_id>/quotes")
def auothor_quotes(author_id):
   """Получение всех цитат автора"""
   author = db.session.scalars(db.select(AuthorModel).where(AuthorModel.id==author_id, AuthorModel.is_deleted==False)).one_or_none()
   
   if not author:
      return jsonify([]), 200

   quotes = []
   for item in author.quotes:
      quotes.append(item.to_dict())

   return jsonify(author=author.to_dict(), quotes=quotes), 200


@app.route("/authors", methods=['POST'])
def create_author():
   """Добавление авторов"""
   data = request.json.copy()
   if not isinstance(data, list):
      data = [data]
   
   fields = ("name", "surname")

   authors = []
   for item in data:
      new_values = (item.get(key) for key in fields)
      if None in new_values:
         abort(HTTPStatus.BAD_REQUEST, "Нерпавильный формат входных данных. Необходимые поля: "+", ".join(fields))

      new_author = AuthorModel(item["name"], item["surname"])
      authors.append(new_author)
   
   if len(authors):
      db.session.add_all(authors)
      db.session.commit()

   return jsonify(result=f"Добавлено авторов: {len(authors)}"), 200


@app.route("/authors/<int:author_id>", methods=["PUT"])
def edit_author(author_id):
   """Редактирование автора"""
   data = request.json.copy()

   author = db.get_or_404(AuthorModel, author_id, description=f"Не найден автор для редактирования с id={author_id}")

   for key in data.keys():
      if hasattr(author, key):
         setattr(author, key, data[key])
      else:
         abort(HTTPStatus.BAD_REQUEST, f"Модель AuthorModel не содержит атрибут {key}")
   db.session.commit()

   return author.to_dict(), 200


@app.route("/authors/<int:author_id>", methods=["DELETE"])
def delete_author(author_id):
   """Удаление автора"""
   author = db.get_or_404(AuthorModel, author_id, description=f"Не найден автор для удаления с id={author_id}")
   author.is_deleted = True
   db.session.commit()

   return jsonify(result=f"Автор с id={author_id} успешно помечен на удаление"), 200


@app.route("/authors/<int:author_id>/quotes", methods=['POST'])
def create_quote(author_id):
   """Добавление цитат автора"""
   data = request.json.copy()
   if not isinstance(data, list):
      data = [data]
   
   author = db.get_or_404(AuthorModel, author_id)

   fields = ("text", "rating")

   quotes = []
   for item in data:
      new_values = (item.get(key) for key in fields)
      if None in new_values:
         abort(HTTPStatus.BAD_REQUEST, "Нерпавильный формат входных данных. Необходимые поля: "+", ".join(fields))

      new_quote = QuoteModel(author, item["text"], item["rating"])
      quotes.append(new_quote)
   
   if len(quotes):
      db.session.add_all(quotes)
      db.session.commit()

   return jsonify(result=f"Добавлено цитат автора: {len(quotes)}"), 200


@app.route("/authors/filter")
def filter_authors():
   """Фильтр по авторам"""
   args = {key: value for key, value in request.args.items() if key in ("name", "surname")}
   quotes = db.session.execute(db.select(AuthorModel).where(AuthorModel.is_deleted==False).filter_by(**args)).scalars()
   return jsonify([item.to_dict() for item in quotes]), 200 


@app.route("/authors/all_deleted")
def all_deleted_authors():
   """Получение всех удаленных авторов"""
   authors = db.session.scalars(db.select(AuthorModel).where(AuthorModel.is_deleted==True)).all()
   return jsonify([item.to_dict() for item in authors]), 200


@app.route("/authors/undelete_all", methods=['PUT'])
def undelete_all_authors():
   """Снятие всех пометок удаления с авторов"""
   result = db.session.execute(db.update(AuthorModel).where(AuthorModel.is_deleted==True).values(is_deleted=False))
   db.session.commit()
   return jsonify(result=f"Снято пометок удаления: {result.rowcount}"), 200


"""Quotes"""

@app.route("/quotes")
def quotes_list():
   """Получение всех цитат"""
   quotes_db = db.session.scalars(db.select(QuoteModel,AuthorModel).where(QuoteModel.author_id==AuthorModel.id, AuthorModel.is_deleted==False)).all()
   return jsonify([item.to_dict() for item in quotes_db]), 200


@app.route("/quotes/<int:quote_id>")
def quote_by_id(quote_id):
   """Получение цитаты по id"""
   quote = db.session.scalars(db.select(QuoteModel,AuthorModel).where(
      QuoteModel.author_id==AuthorModel.id,
      AuthorModel.is_deleted==False,
      QuoteModel.id==quote_id)).one_or_none()

   if quote:
      return quote.to_dict(), 200
   else:
      return jsonify({}), 200
   

@app.route("/quotes/<int:quote_id>", methods=["PUT"])
def edit_qoute(quote_id):
   """Редактирование цитаты по id"""
   data = request.json.copy()

   quote = db.get_or_404(QuoteModel, quote_id, description=f"Не найдена цитата для редактирования с id={quote_id}")

   for key in data.keys():
      if not hasattr(quote, key):
         abort(HTTPStatus.BAD_REQUEST, f"Модель QuoteModel не содержит атрибут {key}") 

   author = db.get_or_404(AuthorModel, data["author_id"], description=f"Не найден автор с id={data["author_id"]}")

   quote.author = author
   quote.text = data["text"]
   quote.rating = QuoteModel.validate_rating(data["rating"], default=quote.rating)
   db.session.commit()

   return quote.to_dict(), 200


@app.route("/quotes/<int:quote_id>", methods=["DELETE"])
def delete_quote(quote_id):
   """Удаление цитаты по id"""
   quote = db.get_or_404(QuoteModel, quote_id, description=f"Не найдена цитата для удаления с id={quote_id}")
   db.session.delete(quote)
   db.session.commit()

   return jsonify(result=f"Цитата с id={quote_id} успешно удалена"), 200


@app.route("/quotes/filter")
def filter_quotes():
   """Фильтр по цитатам"""
   args = {key: value for key, value in request.args.items() if key in ("author_id", "rating")}
   quotes = db.session.execute(db.select(QuoteModel, AuthorModel).where(
      AuthorModel.id==QuoteModel.author_id,
      AuthorModel.is_deleted==False).filter_by(**args)).scalars()

   return jsonify([item.to_dict() for item in quotes]), 200 


@app.route("/quotes/<int:quote_id>/inc_rating", methods=["PUT"])
def inc_qoute_rating(quote_id):
   """Инкремент рейтинга"""
   quote = db.get_or_404(QuoteModel, quote_id, description=f"Не найдена цитата для редактирования с id={quote_id}") 
   quote.edit_rating(lambda x: x + 1)
   db.session.commit()

   return quote.to_dict(), 200


@app.route("/quotes/<int:quote_id>/dec_rating", methods=["PUT"])
def dec_qoute_rating(quote_id):
   """Декремент рейтинга"""
   quote = db.get_or_404(QuoteModel, quote_id, description=f"Не найдена цитата для редактирования с id={quote_id}")
   quote.edit_rating(lambda x: x - 1)
   db.session.commit()

   return quote.to_dict(), 200


if __name__ == "__main__":
   app.run(debug=True)