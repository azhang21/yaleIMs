import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from passlib.apps import custom_app_context as CryptContext

from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.route("/")
def index():
    return render_template("homepage.html")


@app.route("/updatestandings", methods=["GET", "POST"])
@login_required
def updatestandings():
    if request.method == "POST":

        if not request.form.get("college"):
            return apology("must provide a sport", 400)

        if not request.form.get("sport"):
            return apology("must provide valid sport", 400)

        if not request.form.get("points"):
            return apology("must provide valid points", 400)

        college = request.form.get("college")
        sport = request.form.get("sport")
        points = int(request.form.get("points"))

        rows = db.execute("SELECT * FROM standings WHERE sport = :sport AND college = :college", sport=sport, college=college)
        row = rows[0]
        current = int(row['points'])

        db.execute("UPDATE standings SET points = :points WHERE sport = :sport AND college = :college", points=current+points, sport=sport, college=college)

        return redirect("/standings")

    else:
        return redirect("/updatestandings")


@app.route("/standings", methods=["GET", "POST"])
def standings():
    if request.method == "POST":
        soccer = db.execute("SELECT * FROM standings ORDER BY points WHERE sport = :sport", sport="soccer")
        tabletennis = db.execute("SELECT * FROM standings ORDER BY points WHERE sport = :sport", sport="tabletennis")
        volleyball = db.execute("SELECT * FROM standings ORDER BY points WHERE sport = :sport", sport="volleyball")
        pickleball = db.execute("SELECT * FROM standings ORDER BY points WHERE sport = :sport", sport="pickleball")
        crosscountry = db.execute("SELECT * FROM standings ORDER BY points WHERE sport = :sport", sport="crosscountry")

        overall = db.execute("SELECT college,SUM(points) FROM standings GROUP BY college ORDER BY SUM(points)")

        counter = 0
        for i in range(14):
            counter = counter+1

        return render_template("standings.html", counter=counter, soccer=soccer, tabletennis=tabletennis, volleyball=volleyball, pickleball=pickleball, crosscountry=crosscountry)

    else:
        return redirect("/standings")



@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 400)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
