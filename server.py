"""Movie Ratings."""

from jinja2 import StrictUndefined

from flask import Flask, render_template, redirect, request, flash, session 
from flask_debugtoolbar import DebugToolbarExtension

from model import connect_to_db, db, User, Rating, Movie


app = Flask(__name__)
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"

# Normally, if you use an undefined variable in Jinja2, it fails silently.
# This is horrible. Fix this so that, instead, it raises an error.
app.jinja_env.undefined = StrictUndefined


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
            return redirect("/users/"+str(db_user.user_id))
        else:
            flash("Incorrect password.")
            # flash message alerting them to incorrect password
            # redirect back to homepage
            return render_template("homepage.html")
    else: 
        # make uswer
        new_user = User(email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        session['logged_in_email'] = email
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
    return render_template("homepage.html")


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

    movie = db.session.query(Movie).filter_by(title=title).first()

    score_info = db.session.query(Movie.title,
                                  User.email,
                                  Rating.score).filter_by(title=title).join(Rating).join(User).all()

    all_scores = []
    for score in score_info:
        all_scores.append(int(score[2]))
    avg_score = round(float(sum(all_scores)) / len(all_scores), 1)

    user_score = None
    for tup in score_info:
        if session.get("logged_in_email"):
            if tup[1] == session["logged_in_email"]:
                user_score = tup[2]

    return render_template("movie.html",
                           movie=movie,
                           score_info=score_info,
                           avg_score=avg_score,
                           user_score=user_score)

@app.route('/submit-rating', methods=["POST"])
def submit_user_rating():
    """adds a new rating or edits an existing rating to the database"""

    user_email = request.form.get('user-email')
    movie_id = request.form.get('movie-id')

    # if user has a score, change the database
    # if user is new to scores this movie, create a score
    # use AJAX so user is not directed to a new page (in HTML)



if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the point
    # that we invoke the DebugToolbarExtension
    app.debug = True

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run()
