"""Movie Ratings."""

from jinja2 import StrictUndefined

from flask import Flask, render_template, redirect, request, flash, session, jsonify
from flask_debugtoolbar import DebugToolbarExtension

from model import connect_to_db, db, User, Rating, Movie



app = Flask(__name__)
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"

# Normally, if you use an undefined variable in Jinja2, it fails silently.
# This is horrible. Fix this so that, instead, it raises an error.
app.jinja_env.undefined = StrictUndefined

THE_EYE_EMAIL = "the-eye@of-judgement.com"

BERATEMENT_MESSAGES = [
        "I suppose you don't have such bad taste after all.",
        "I regret every decision that I've ever made that has brought me" +
            " to listen to your opinion.",
        "Words fail me, as your taste in movies has clearly failed you.",
        "That movie is great. For a clown to watch. Idiot.",
        "Words cannot express the awfulness of your taste."
    ]

@app.route('/')
def index():
    """Homepage."""

    return render_template("homepage.html")


@app.route('/users')
def user_list():
    """Show list of users."""

    users = User.query.all()
    return render_template("user_list.html", users=users)


@app.route('/movies')
def list_movies():
    """shows a list of all movies with links to each movie's page"""

    movies = db.session.query(Movie).all()
    movies_lists = []
    for movie in movies:
        if movie.released_at:
            movies_lists.append([movie.title, movie.released_at.strftime("%b %d, %Y")])
        elif movie.title:
            movies_lists.append([movie.title, "unknown"])

    movies_lists.sort()

    return render_template("movies.html", movies=movies_lists)



@app.route('/login', methods=["POST"])
def login():
    """Handles user login"""

    email = request.form.get('email')
    password = request.form.get('password')
    print email, password
    db_user = db.session.query(User).filter(User.email==email).first()
    print db_user

    if db_user:
        if password == db_user.password:
            # flash message
            # return render_template("homepage.html")
            # add username to session
            flash("Successfully logged in.")
            session['logged_in_email'] = db_user.email
            session['logged_in_user_id'] = db_user.user_id
            return redirect("/users/"+str(db_user.user_id))
        else:
            flash("Incorrect password.")
            # flash message alerting them to incorrect password
            # redirect back to homepage
            return redirect("/")
    else: 
        # make uswer
        new_user = User(email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        session['logged_in_email'] = email
        session['logged_in_user_id'] = new_user.user_id
        flash("You've been added and you are logged in.")
        return redirect("/users/"+str(new_user.user_id))


@app.route('/logout')
def logout():
    """logs user out"""

    # removes user from session
    session.pop("logged_in_email", None)

    # gives user feedback on their logout action
    flash("You have been logged out.")

    # routes to homepage
    return redirect("/")


@app.route('/users/<int:user_id>')
def show_user_info(user_id):

    user = User.query.get(user_id)

    # Write query to get movie title and rating score for relevant user id
    movie_ratings = db.session.query(Rating.score, 
                                     Movie.title).filter_by(user_id=user_id).join(Movie).all()


    # Assign an identifier to the result of our query.all()

    return render_template("user.html", user=user, ratings=movie_ratings)


@app.route('/movies/<title>')
def show_movie_info(title):

    # gets a movie object based on title
    movie = db.session.query(Movie).filter_by(title=title).first()
    # gets a user id from the logged in user
    user_id = session.get("logged_in_user_id")
    # makes a list of tuples: (title, user_email, score)
    score_info = db.session.query(Movie.title,
                                  User.email,
                                  Rating.score).filter_by(title=title).join(Rating).join(User).all()
    # finds average score for current movie
    all_scores = [int(score_item[2]) for score_item in score_info]
    avg_score = round(float(sum(all_scores)) / len(all_scores), 1)
    # getting the current user's score of the current movie, if they rated it
    user_score = None
    for tup in score_info:
        if session.get("logged_in_email"):
            if tup[1] == session["logged_in_email"]:
                user_score = tup[2]
    # if user hasn't rated movie, assigns prediction
    prediction = None
    if (not user_score) and user_id:
        user = User.query.get(user_id)
        if user:
            # Could be None if not enough relevant correlations were found
            # typically a float
            prediction = user.predict_rating(movie.movie_id)
    # If a valid prediction was created, clean up number
    # Else use prediction_failed to convey failure message
    if prediction:
        prediction = round(prediction, 1)
        prediction_failed = None
    else:
        prediction_failed = "Not enough ratings to predict your rating of this movie."
    # deals with the eye and it's beratement
    beratement = None
    if user_score:
        # gets eye object and rating for current movie
        the_eye = db.session.query(User).filter_by(email=THE_EYE_EMAIL).one()
        eye_rating = db.session.query(Rating).filter(Rating.user_id==the_eye.user_id,
                        Rating.movie_id==movie.movie_id).first()
        # use's eye's rating or assigns prediction to eye's rating
        if eye_rating is None:
            eye_prediction = the_eye.predict_rating(movie.movie_id)
            if eye_prediction is None:
                eye_prediction = abs(avg_score - 6)
        else:
            eye_prediction = eye_rating.score
        # finds the difference between the eye and the user's ratings for beratment
        if eye_prediction and user_score:
            difference = abs(eye_prediction - user_score)
            beratement = (BERATEMENT_MESSAGES[int(difference)] + 
                          "The Eye would score this movie a " + 
                          str(round(eye_prediction,1)))
            

    return render_template("movie.html",
                           movie=movie,
                           release_date=movie.released_at.strftime("%b %d, %Y"),
                           score_info=score_info,
                           avg_score=avg_score,
                           user_score=user_score,
                           prediction=prediction,
                           prediction_failed=prediction_failed,
                           beratement=beratement)

@app.route('/submit-rating', methods=["POST"])
def submit_user_rating():
    """adds a new rating or edits an existing rating to the database"""
    movie_id = request.form.get('movie-id')
    movie = Movie.query.get(movie_id)

    if not session.get("logged_in_email"):
        flash("You need to log in to rate movies.")
        return redirect("/movies/"+str(movie.title))
    # gets user_email, movie_id, and score from the rating form submission
    user_email = request.form.get('user-email')
    users_score = request.form.get('user-rating')
    # get user_id from db using user_email
    user_id = db.session.query(User).filter(user_email==User.email).first().user_id
    # get user rating object from db (for specific user and movie id)
    users_rating = db.session.query(Rating).filter(Rating.movie_id==movie_id,
                                                   Rating.user_id==user_id).first()
    

    updateMessage = ""
    # check if user has previously rated movie
    if users_rating:
        # update previous rating
        users_rating.score = users_score
        updateMessage = "Your rating has been updated to " + str(users_score)
    # create new rating instance for specific user and movie id
    else:
        users_rating = Rating(user_id=user_id,
                              movie_id=movie_id,
                              score=users_score)
        # Add rating instance to db
        db.session.add(users_rating)
        updateMessage = "A new score of " + str(users_score) + " has been added."
    # Commit new score or new Rating object to db
    db.session.commit()
    # Create dictionary indicating success
    # returnValue = {"message": updateMessage, "score": users_score}
    # return jsonify(returnValue)
    return redirect("/movies/"+str(movie.title))
    





if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the point
    # that we invoke the DebugToolbarExtension
    app.debug = True

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run()
