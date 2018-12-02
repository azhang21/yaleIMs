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


@app.route("/")
def index():
    return render_template("homepage.html")


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
        add = db.execute("INSERT INTO contact(year, season, college, name, email, sport) VALUES(:year, :season, :college, :name, :email, :sport)",
                         year=request.form.get("year"), season=request.form.get("season"), college=request.form.get("college"),
                         name=request.form.get("name"), email=request.form.get("email"), sport=request.form.get("sport"))
        if not add:
            return apology("unsuccessful", 403)

        return render_template("updatepage.html")

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

        # Remember which user has logged in
        session["user_id"] = "yaleims18"

        # allow im sec to choose what command to execute
        return render_template("updatepage.html")

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
        if not request.form.get("year") or not request.form.get("season") or not request.form.get("college") or not request.form.get("sport"):
            return apology("must select year/season/college/sport", 403)

        names = []
        emails =[]

        # Ensure combination of year, season, college exists - get im secretaries
        if request.form.get("sport") == "N-A":
            imsecs = db.execute("SELECT name, email FROM contact WHERE year=:yr AND season=:szn AND college=:col",
                               yr=request.form.get("year"), szn=request.form.get("season"), col=request.form.get("college"))
            if not imsecs:
                return apology("no current student leadership", 403)
            # submit user's input to /searched
            else:
                for imsec in imsecs:
                    names.append(imsec["name"])
                    emails.append(imsec["email"])
                position = "IM Secretary"
                leng = len(names)
                return render_template("searched.html", season=request.form.get("season"), year=request.form.get("year"),
                                       college=request.form.get("college"), names=names, emails=emails, position=position, leng=leng)
        # Ensure combination of year, season, college, sport exists if sports field is chosen - get captains
        captains = db.execute("SELECT name, email FROM contact WHERE year=:yr AND season=:szn AND college=:col AND sport=:spo",
                              yr=request.form.get("year"), szn=request.form.get("season"), col=request.form.get("college"), spo=request.form.get("sport"))
        if not captains:
            return apology("no current student leadership", 403)
        else:
            for cap in captains:
                names.append(cap["name"])
                emails.append(cap["email"])
            position = "Captain"
            leng = len(names)
            return render_template("searched.html", season=request.form.get("season"), year=request.form.get("year"),
                                   college=request.form.get("college"), sport=request.form.get("sport"), names=names, emails=emails, position=position, leng=leng)

    else:
        # put existing 'contact' into search form
        contact = db.execute("SELECT year, season, college, sport FROM contact")

        # get arrays of existing year, season, college, sport to insert into dropdown menus
        yrs = []
        szn = []
        col = []
        sport = []
        for contac in contact:
            if contac["year"] not in yrs:
                yrs.append(contac["year"])
            if contac["season"] not in szn:
                szn.append(contac["season"])
            if contac["college"] not in col:
                col.append(contac["college"])
            if contac["sport"] not in sport:
                sport.append(contac["sport"])

        return render_template("search.html", yrs=yrs, szn=szn, col=col, sport=sport)


@app.route("/delete", methods=["GET", "POST"])
@login_required
def delete():
    """Obtain a list of IM Secs and/or Captains to eventually delete"""
    if request.method == "POST":

        # Ensure email, sport selections were made
        if not request.form.get("email") or not request.form.get("sport"):
            return apology("must provide email/sport", 403)

        # delete relevant im sec / cap
        delete = db.execute("DELETE FROM contact WHERE email=:email AND sport=:sport",
                           email=request.form.get("email"), sport=request.form.get("sport"))

        if not delete:
            return apology("person does not exist in database", 403)

        return render_template("updatepage.html")

    else:
        return render_template("delete.html")


@app.route("/standings")
def standings():

    soccer = db.execute("SELECT * FROM standings WHERE sport = 'soccer' ORDER BY -points")
    tabletennis = db.execute("SELECT * FROM standings WHERE sport = 'table tennis' ORDER BY -points")
    volleyball = db.execute("SELECT * FROM standings WHERE sport = 'volleyball' ORDER BY -points")
    pickleball = db.execute("SELECT * FROM standings WHERE sport = 'pickleball' ORDER BY -points")
    crosscountry = db.execute("SELECT * FROM standings WHERE sport = 'cross country' ORDER BY -points")

    overall = db.execute("SELECT college,SUM(points) FROM standings GROUP BY college ORDER BY -SUM(points)")

    return render_template("standings.html", soccer=soccer, tabletennis=tabletennis, volleyball=volleyball, pickleball=pickleball, crosscountry=crosscountry, overall=overall)



@app.route("/updatepage", methods=["GET", "POST"])
@login_required
def updatepage():
    if request.method == "POST":

        if not request.form.get("options"):
            return apology("must choose an option", 400)

        option = request.form.get("options")

        if option == "points":
            return render_template("updatestandings.html")

        if option == "add":
            return render_template("add.html")

        if option == "delete":
            return render_template("delete.html")

    else:
        return render_template("updatepage.html")


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

        if len(rows) > 0:
            row = rows[0]
            current = int(row['points'])
            db.execute("UPDATE standings SET points = :points WHERE sport = :sport AND college = :college", points=current+points, sport=sport, college=college)

        else:
            db.execute("INSERT INTO standings(college, sport, points) VALUES(:college, :sport, :points)", college=college, sport=sport, points=points)

        return redirect("/standings")

    else:
        return render_template("updatestandings.html")


def errorhandler(e):
    """Handle error"""
    return apology("AHHH", 314)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
