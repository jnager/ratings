"""Utility file to seed ratings database from MovieLens data in seed_data/"""

from sqlalchemy import func
from model import User
from model import Rating
from model import Movie

from model import connect_to_db, db
from server import app
import datetime


def load_users():
    """Load users from u.user into database."""

    print "Users"

    # Delete all rows in table, so if we need to run this a second time,
    # we won't be trying to add duplicate users
    User.query.delete()

    # Read u.user file and insert data
    for row in open("seed_data/u.user"):
        row = row.rstrip()
        user_id, age, gender, occupation, zipcode = row.split("|")

        user = User(user_id=user_id,
                    age=age,
                    zipcode=zipcode)

        # We need to add to the session or it won't ever be stored
        db.session.add(user)

    # Once we're done, we should commit our work
    db.session.commit()


def load_movies():
    """Load movies from u.item into database."""

    # Delete all ros in table so there won't be dupes
    Movie.query.delete()

    # read u.item file and insert data 
    for row in open("seed_data/u.item"):
        row = row.rstrip()
        movie_data = row.split("|")
        movie_id = movie_data[0]
        # Handle movie title to remove year and convert to unicode
        title = movie_data[1]
        title = title[:-7]
        title = title.decode("latin-1")
        # Convert date as supplied into a datetime object
        released_str = movie_data[2]
        if released_str:
            released_at = datetime.datetime.strptime(released_str, "%d-%b-%Y")
        else:
            released_at = None
        imdb_url = movie_data[4]

        # creates an instance of the Movie class for each movie 
        movie = Movie(movie_id=movie_id,
                      title=title,
                      released_at=released_at,
                      imdb_url=imdb_url)

        # add each movie to the session db
        db.session.add(movie)

    # commit changes to db
    db.session.commit()


def load_ratings():
    """Load ratings from u.data into database."""
    # Clears table of existing rows
    Rating.query.delete()

    # Read u.data and insert data
    for row in open("seed_data/u.data"):
        row = row.rstrip()
        user_id, movie_id, score, timestamp = row.split("\t")
        # Create an instance of Rating using info from seed data file
        rating = Rating(user_id=user_id,
                        movie_id=movie_id,
                        score=score)
        # Add rating instance to db
        db.session.add(rating)
    # Commit work to db
    db.session.commit()


def set_val_user_id():
    """Set value for the next user_id after seeding database"""

    # Get the Max user_id in the database
    result = db.session.query(func.max(User.user_id)).one()
    max_id = int(result[0])

    # Set the value for the next user_id to be max_id + 1
    query = "SELECT setval('users_user_id_seq', :new_id)"
    db.session.execute(query, {'new_id': max_id + 1})
    db.session.commit()


if __name__ == "__main__":
    connect_to_db(app)

    # In case tables haven't been created, create them
    db.create_all()

    # Import different types of data
    load_users()
    print "Finished load_users"
    load_movies()
    print "Finished load_movies"
    load_ratings()
    print "Finished load_ratings"
    set_val_user_id()
    print "Done!"
