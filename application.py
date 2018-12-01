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

        # Ensure "symbol" isn't blank
        if not request.form.get("symbol"):
            return apology("must provide symbol", 403)

        # Ensure "symbol" exists
        quote = lookup(request.form.get("symbol"))
        if not quote:
            return apology("invalid symbol", 400)

        # ensure "shares" isn't blank
        if not request.form.get("shares"):
            return apology("must provide shares", 400)

        # ensure "shares" is a positive integer
        if not (request.form.get("shares")).isdigit():
            return apology("shares not a number", 400)

        if int(request.form.get("shares")) < 1:
            return apology("shares not positive", 400)

        # check that user has enough cash to complete transaction
        money = db.execute("SELECT cash FROM users WHERE id=:id", id=session["user_id"])
        if (quote["price"] * float(request.form.get("shares"))) > money[0]["cash"]:
            return apology("Not enough cash to complete purchase", 400)

        # after validation, buy
        sold = db.execute("INSERT INTO histories (id, symbol, name, shares, price, total) VALUES (:id, :symbol, :name, :shares, :price, :total)",
                          id=session["user_id"], symbol=quote["symbol"], name=quote["name"], shares=request.form.get("shares"),
                          price=quote["price"], total=float(request.form.get("shares"))*quote["price"])

        # subtract from cash
        subtract = db.execute("UPDATE users SET cash=:cash WHERE id=:id", id=session["user_id"], cash=(
                              money[0]["cash"]-quote["price"] * float(request.form.get("shares"))))

        return redirect("/")

    else:
        return render_template("buy.html")

### incorporate only if finish everything else: check if IM Sec / captain email already entered, jsonify v v confusing tho
@app.route("/check", methods=["GET"])
def check():
    """Return true if username available, else false, in JSON format"""
    user = request.args.get('username')
    belong = db.execute("SELECT * FROM users WHERE username=:username",
                        username=user)

    # ensure username is at least one character and not in database
    if len(user) < 1 or belong:
        return jsonify(False)
    else:
        return jsonify(True)


@app.route("/history")
def subset():
    """Show subset of database according to college / year / season / sport"""
    # create subset of 'histories' that belongs to user
    portfolios = db.execute("SELECT symbol, shares, price, transacted FROM histories WHERE id=:id", id=session["user_id"])

    return render_template("history.html", portfolios=portfolios)


@app.route("/imsecHome", methods=["GET"])
@login_required
def imsecHome():
    """Page where IM Sec selects what they want to update - points or contact info"""


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
            secEmails = []
            for imsec in imsecs:
                secs.append(imsecs["imsec"])
                secEmails.append(imsecs["imsec_email"])

            caps = []
            return render_template("searched.html", name=quote["name"], symbol=quote["symbol"], price=usd(quote["price"]))
        else if imsecs:
            return render_template("searched.html", )
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


@app.route("/buy", methods=["GET", "POST"])
@login_required
def update():
    """Buy shares of stock"""
    if request.method == "POST":

        # Ensure "symbol" isn't blank
        if not request.form.get("symbol"):
            return apology("must provide symbol", 403)

        # Ensure "symbol" exists
        quote = lookup(request.form.get("symbol"))
        if not quote:
            return apology("invalid symbol", 400)

        # ensure "shares" isn't blank
        if not request.form.get("shares"):
            return apology("must provide shares", 400)

        # ensure "shares" is a positive integer
        if not (request.form.get("shares")).isdigit():
            return apology("shares not a number", 400)

        if int(request.form.get("shares")) < 1:
            return apology("shares not positive", 400)

        # check that user has enough cash to complete transaction
        money = db.execute("SELECT cash FROM users WHERE id=:id", id=session["user_id"])
        if (quote["price"] * float(request.form.get("shares"))) > money[0]["cash"]:
            return apology("Not enough cash to complete purchase", 400)

        # after validation, buy
        sold = db.execute("INSERT INTO histories (id, symbol, name, shares, price, total) VALUES (:id, :symbol, :name, :shares, :price, :total)",
                          id=session["user_id"], symbol=quote["symbol"], name=quote["name"], shares=request.form.get("shares"),
                          price=quote["price"], total=float(request.form.get("shares"))*quote["price"])

        # subtract from cash
        subtract = db.execute("UPDATE users SET cash=:cash WHERE id=:id", id=session["user_id"], cash=(
                              money[0]["cash"]-quote["price"] * float(request.form.get("shares"))))

        return redirect("/")

    else:
        return render_template("buy.html")


def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)