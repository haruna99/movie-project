from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests

API_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJmOGEyNTQ1YmU3NTMwOGUzYjc3OGRmYjZlZWRiZDgyMSIsInN1YiI6IjYyZTVmMjMyYmQ1ODhi" \
          "MDA1OTAxZDEwOCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.rW5LlXzppccr-IHE7K9rALiGuBqaAWsXeT_DYFRXasg"
API_URL = 'https://api.themoviedb.org/3'
headers = {
    'Authorization': f'Bearer {API_TOKEN}',
    'Content-Type': 'application/json;charset=utf-8'
}
IMAGE_URL = "https://image.tmdb.org/t/p/w500"

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///favorite-movies.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


class Movies(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), unique=True, nullable=False)
    year = db.Column(db.String(4), nullable=False)
    description = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Float)
    ranking = db.Column(db.Integer)
    review = db.Column(db.String(200))
    img_url = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"<Movie {self.title}>"


db.create_all()

db.session.commit()


class EditForm(FlaskForm):
    rating = StringField(label="Your rating out of 10 e.g 7.5", validators=[DataRequired()])
    review = StringField(label="Your review", validators=[DataRequired()])
    submit = SubmitField(label="Done")


class AddForm(FlaskForm):
    title = StringField(label="Movie Title", validators=[DataRequired()])
    submit = SubmitField(label="Add Movie")


@app.route("/")
def home():
    movies = Movies.query.order_by("rating").all()
    for i in range(len(movies)):
        movies[i].ranking = len(movies) - i
    db.session.commit()
    return render_template("index.html", movies=movies)


@app.route("/edit/<int:movie_id>", methods=["GET", "POST"])
def edit(movie_id):
    form = EditForm()
    get_movie = Movies.query.get(movie_id)
    if form.validate_on_submit():
        get_movie.rating = form.rating.data
        get_movie.review = form.review.data
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("edit.html", form=form, movie=get_movie)


@app.route("/delete/<int:movie_id>")
def delete(movie_id):
    movie = Movies.query.get(movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/add", methods=["GET", "POST"])
def add():
    form = AddForm()
    if form.validate_on_submit():
        params = {
            "query": form.title.data
        }
        response = requests.get(url=f"{API_URL}/search/movie", params=params, headers=headers)
        data = response.json()
        movies = data["results"]
        return render_template("select.html", movies=movies)
    return render_template("add.html", form=form)


@app.route("/select/<int:movie_id>")
def select(movie_id):
    params = {
        "language": "en-US"
    }
    response = requests.get(url=f"{API_URL}/movie/{movie_id}", params=params, headers=headers)
    data = response.json()
    new_movie = Movies(
        title=data["title"],
        img_url=f"{IMAGE_URL}{data['poster_path']}",
        year=data["release_date"].split("-")[0],
        description=data["overview"],
    )
    db.session.add(new_movie)
    db.session.commit()
    movie = Movies.query.filter_by(title=data["title"]).first()
    return redirect(url_for("edit", movie_id=movie.id))


if __name__ == '__main__':
    app.run(debug=True)
