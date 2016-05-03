"""Movie Ratings."""

from jinja2 import StrictUndefined

from flask import Flask, render_template, redirect, request, flash, session 
from flask_debugtoolbar import DebugToolbarExtension

from model import connect_to_db, db, User, Rating, Movie


app = Flask(__name__)

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
            return render_template("homepage.html")
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
        return render_template("homepage.html")

@app.route('/logout')
def logout():
    """logs user out"""

    # removes user from session
    session.pop("logged_in_email", None)

    # gives user feedback on their logout action
    flash("You have been logged out.")

    # routes to homepage
    return render_template("homepage.html")


@app.route('/users/<user_id>')
def show_user_info(user_id):

    user = User.query.get(user_id)

    # Write query to get movie title and rating score for relevant user id
    movie_ratings = db.session.query(User.user_id, 
                                     Movie.title, 
                                     Rating.score).filter_by(user_id=user_id).join(Rating).join(Movie).all()


    # Assign an identifier to the result of our query.all()

    return render_template("user.html", user=user, ratings=movie_ratings)


if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the point
    # that we invoke the DebugToolbarExtension
    app.debug = True

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run()
