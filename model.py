"""Models and database functions for Ratings project."""

from flask_sqlalchemy import SQLAlchemy
import correlation 

# This is the connection to the PostgreSQL database; we're getting this through
# the Flask-SQLAlchemy helper library. On this, we can find the `session`
# object, where we do most of our interactions (like committing, etc.)

db = SQLAlchemy()


##############################################################################
# Model definitions

class User(db.Model):
    """User of ratings website."""

    __tablename__ = "users"

    user_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    email = db.Column(db.String(64), nullable=True)
    password = db.Column(db.String(64), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    zipcode = db.Column(db.String(15), nullable=True)

    def similarity(self, other):
        """Return Pearson rating for user compared to other User."""
        
        # create a dictionary to store current user's {movie_id: score}
        u_ratings = {}
        # create a list to store tuples of 
        # (current user's rating, other user's rating)
        paired_ratings = []
        
        # loop through all Rating object of current user to add to 
        # the recently created dictionary of his/her movie scores
        for r in self.ratings:
            u_ratings[r.movie_id] = r
        
        # loop through other user's list of Rating objects
        for r in other.ratings:
            # get Rating object for any movies that match a movie
            # that the current user has already rated
            u_r = u_ratings.get(r.movie_id)
            # if there is a Rating object with the same movie id...
            if u_r:
                # create a tuple with (other's score, user's score)
                paired_ratings.append( (u_r.score, r.score) )
        
        # after looping all Ratings, if there were any movie matches, 
        # run the Pearson correlation math with the matches
        # return the correlation value between other & current users
        if paired_ratings:
            return correlation.pearson(paired_ratings)
        # if no same movies were rated, return a correlation of 0
        else:
            return 0.0


    def predict_rating(self, movie_id):
        """Predicts what a user will rate a movie, 
        assuming they haven't yet rated it"""

        # returns a list of Rating objects for all users who have rated the movie in question
        other_ratings = db.session.query(Rating).filter(Rating.movie_id==movie_id).all()
        # makes a list to store tuples of correlations and user id's
        correlations = []
        # make a list of correlations and user id's
        for rating in other_ratings:
            correlations.append((self.similarity(rating.user), rating))
        # sort users by correlation with current user
        correlations.sort(reverse=True)
        # removes negatively correlated ratings from the list
        correlations = [(sim, rating) for sim, rating in correlations if sim > 0]
        # if no positively correlated users, return None
        if not correlations:
            return None
        # do statistical math
        numerator = sum([rating.score * sim for sim, rating in correlations])
        denominator = sum([sim for sim, rating in correlations])
        
        return numerator/denominator


    def __repr__(self):
        """Provide helpful representation when printed."""

        return "<User user_id=%s email=%s>" % (self.user_id, self.email)
        


class Movie(db.Model):
    """Movies"""

    __tablename__ = "movies"

    movie_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(128), nullable=False)
    released_at = db.Column(db.DateTime, nullable=True)
    imdb_url = db.Column(db.String(256), nullable=True)

    def __repr__(self):
        """Provide helpful representation when printed."""

        return "<Movie movie_id=%s title=%s>" % (self.movie_id, self.title)


class Rating(db.Model):
    """Ratings from user by movie."""

    __tablename__ = "ratings"

    rating_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    movie_id = db.Column(db.Integer,
                         db.ForeignKey('movies.movie_id'),
                         nullable=False)
    user_id = db.Column(db.Integer,
                        db.ForeignKey('users.user_id'),
                        nullable=False)
    score = db.Column(db.Integer, nullable=False)

    user = db.relationship("User",
                            backref=db.backref("ratings", order_by=rating_id))

    movie = db.relationship("Movie",
                            backref=db.backref("ratings", order_by=rating_id))

    def __repr__(self):
        """Provide helpful representation when printed."""

        return "<Rating rating_id=%s movie_id=%s user_id=%s score=%s>" % (
            self.rating_id, self.movie_id, self.user_id, self.score)




##############################################################################
# Helper functions

def connect_to_db(app):
    """Connect the database to our Flask app."""

    # Configure to use our PstgreSQL database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///ratings'
    db.app = app
    db.init_app(app)


if __name__ == "__main__":
    # As a convenience, if we run this module interactively, it will leave
    # you in a state of being able to work with the database directly.

    from server import app
    connect_to_db(app)
    print "Connected to DB."
