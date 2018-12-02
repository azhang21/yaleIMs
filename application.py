import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions

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
db = SQL("sqlite:///yaleIMs.db")


@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    """Add IM Secretary or Captain"""
    if request.method == "POST":

        # Ensure "year" isn't blank
        if not request.form.get("year"):
            return apology("must select year", 403)

        # Ensure "season" isn't blank
        if not request.form.get("season"):
            return apology("must select season", 403)

        # ensure "college" isn't blank
        if not request.form.get("college"):
            return apology("must select college", 403)

        # ensure "name" isn't blank
        if not request.form.get("name"):
            return apology("must provide name", 403)

        # ensure "email" isn't blank
        if not request.form.get("email"):
            return apology("must provide email", 403)

        # ensure "sport" isn't blank
        if not request.form.get("sport"):
            return apology("must select sport", 403)

        # add into database
        # add as IM secretary
        if request.form.get("sport") == "n-a":
            add = db.execute("INSERT INTO contacts (year, season, college, imsec, imsec_email) VALUES (:yr, :szn, :col, :name, :email)",
                              yr=request.form.get("year"), szn=request.form.get("season"), col=request.form.get("college"),
                              name=request.form.get("name"), email=request.form.get("email"))
        # add as captain
        else:
            add = db.execute("INSERT INTO contacts (year, season, college, sport, captain, captain_email) VALUES (:yr, :szn, :col, :spo, :name, :email)",
                              yr=request.form.get("year"), szn=request.form.get("season"), col=request.form.get("college"),
                              spo=request.form.get("sport"), name=request.form.get("name"), email=request.form.get("email"))

        return redirect("/imsecHome")

    else:
        return render_template("add.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log IM secretary in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Ensure username exists and password is correct
        if request.form.get("username") != "yaleims18" or request.form.get("password") != "yaleims18":
            return apology("invalid username and/or password", 403)

        # Redirect user to home page
        return redirect("/imsecHome")

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


@app.route("/search", methods=["GET", "POST"])
def search():
    """Get contact info of relevant IM Secs and/or Captains"""
    if request.method == "POST":

        # Ensure year, season, college selections were made
        if not request.form.get("year") or not request.form.get("season") or not request.form.get("college"):
            return apology("must select year/season/college", 403)

        # Ensure combination of year, season, college exists - get im secretaries
        imsecs = db.execute("SELECT imsec, imsec_email FROM contacts WHERE yr=:yr AND szn=:szn AND col=:col",
                           yr=request.form.get("year"), szn=request.form.get("season"), col=request.form.get("college"))
        # Ensure combination of year, season, college, sport exists if sports field is chosen - get captains
        if not request.form.get("sport"):
            captains = db.execute("SELECT captain, captain_email FROM contacts WHERE yr=:yr AND szn=:szn AND col=:col AND spo=:spo",
                              yr=request.form.get("year"), szn=request.form.get("season"), col=request.form.get("college"), spo=request.form.get("sport"))


        # submit user's input to /searched
        if imsecs and captains:
            secs = []
            for imsec in imsecs:
                secs.append(imsecs["imsec"]["imsec_email"])

            caps = []
            for cap in captains:
                caps.append(captains["captain"]["captain_email"])

            return render_template("searched.html", season=request.form.get("season"), year=request.form.get("year"),
                                   college=request.form.get("college"), sport=request.form.get("sport"), secs=secs, caps=caps)
        if imsecs:
            secs = []
            for imsec in imsecs:
                secs.append(imsecs["imsec"]["imsec_email"])

            return render_template("searched1.html", season=request.form.get("season"), year=request.form.get("year"),
                                   college=request.form.get("college"), sport=request.form.get("sport"), secs=secs)
        else:
            return apology("invalid combination", 400)


    else:
        # put existing 'contacts' into search form
        contacts = db.execute("SELECT year, season, college, sport FROM contacts ORDER BY year, season, college, sport")

        # get arrays of existing year, season, colege, sport to insert into dropdown menus
        yrs = []
        szn = []
        col = []
        sport = []
        for contact in contacts:
            yrs.append(contacts["year"])
            szn.append(contacts["season"])
            col.append(contacts["college"])
            # sports column may be null
            if contacts["sport"] != None:
                sport.append(contacts["sport"])

        return render_template("search.html", yrs=yrs, szn=szn, col=col, sport=sport)


@app.route("/delete", methods=["GET", "POST"])
@login_required
def delete():
    """Obtain a list of IM Secs and/or Captains to eventually delete"""
    if request.method == "POST":

        # Ensure email, sport selections were made
        if not request.form.get("email") or not request.form.get("sport"):
            return apology("must provide email/sport", 403)

        # Ensure combination of year, season, college exists - get im secretaries
        delete = db.execute("DELETE * FROM contacts WHERE email=:email AND sport=:sport",
                           email=request.form.get("email"), sport=request.form.get("sport"))

        if not delete:
            return apology("person does not exist in database", 403)

    else:
        return render_template("delete.html")


def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
