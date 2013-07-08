import csv
import sqlite3
from flask import Flask, request, g, render_template

import simplejson as json
import urllib


# configuration
DATABASE = '/tmp/flaskr.db'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

app = Flask(__name__)
app.config.from_object(__name__)

dvdfile = 'DVDs.csv'


def all_rows():
    """ Return list of all rows from file. """
    return [row for row in read_file()]


def read_file():
    """
    Generate row dict as read from CSV file -- but with
    tokenized list of stars since there are often multiple.
    """
    with open(dvdfile, 'r') as open_file:
        row_dict_reader = csv.DictReader(open_file)
        for row in row_dict_reader:
            row['stars'] = tokenize(row['stars'])
            yield row


def tokenize(stringy, delimiter=','):
    """ Turn the raw string into a list of words. """
    return [starname.strip() for starname in stringy.split(delimiter)]


def get_ratings(film):
    """ get ratings for a given title from our database """
    ratings = query_db('select * from rankings where title = ?;', [film])
    return ratings


def save_rating(rating, user, film):
    """ save the rating into our database """
    query = "insert into rankings (name, title, ranking) values (?, ?, ?);"
    get_db().execute(query, [user, film, rating])
    get_db().commit()


def film_is_valid(film):
    """
    Iterate through our file to find a matching film. Return True if a
    match is found; False if not.
    """
    for row in all_rows():
        if row['title'] == film:
            return True
    return False


def get_film(film):
    """
    Iterate through our file to find the matching film.
    """
    match = None
    for row in all_rows():
        if row['title'] == film:
            match = row
    return match


@app.route("/rate/<film>", methods=['POST', 'GET'])
def rate(film):
    """ user can rate. the film """
    message = None
    if request.method == 'POST':
        user = request.form.get('user', 'Anonymouse')
        try:
            rating = request.form['rating']
        except KeyError:
            message = "You need to provide a rating!"
        else:
            save_rating(rating, user, urllib.unquote(film))
            message = "Thanks for the rating"
    return render_template('rate.html', film=film, message=message)


def get_average_rating(film):
    running_total = 0
    ratings = get_ratings(film)
    for (id, user, title, rating) in ratings:
        running_total += rating
    return running_total / len(ratings)


@app.route("/ratings/<film>")
def ratings(film):
    """ Show all user ratings for a film. """
    ratings_list = []
    for rating in get_ratings(urllib.unquote(film)):
        info = {
            'title': rating[2],
            'user': rating[1],
            'rating': rating[3]
            }
        ratings_list.append(info)
    return json.dumps(ratings_list)


@app.route("/info/<film>")
def one(film):
    """ show info about a given film if we have info"""
    response = "Not found"
    # TODO: add average rating
    film_name = urllib.unquote(film)
    if film_is_valid(film_name):
        info_dict = get_film(film_name)
        info_dict['average_rating'] = get_average_rating(film_name)
        return json.dumps(info_dict)
    return response


@app.route("/all")
def list_all():
    """ Return response listing all films
    """
    return json.dumps(all_rows())


@app.route("/rankings")
def rank():
    """
    list ranking of films by rating
    return the ranking and number of votes
    """
    pass


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return rv


def connect_db():
    return sqlite3.connect(app.config['DATABASE'])


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = connect_db()
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def init_db():
    """ Run this only once to create the database from our schema. """
    with close_connection(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


if __name__ == "__main__":
    app.run(debug=True)

