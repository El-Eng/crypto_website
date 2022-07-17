import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for, render_template_string
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
import re
import pandas as pd
from helpers import apology, login_required, usd

dev = False

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

if dev:
    db = SQL("sqlite:///finance.db")
else:
    uri = os.getenv("DATABASE_URL")
    if uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://")
    db = SQL(uri)


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
def index():
    return render_template("index.html")
    #return redirect(url_for('login'))

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
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 400)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Remember username
        temp = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        session["username"] = temp[0]["username"]
        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/home")
@login_required
def home():
    return render_template("home.html", username=session["username"])

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """Update user profile"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Update phone if submitted
        if request.form.get("phone"):
            # Upload phone to database
            db.execute("UPDATE users SET phone = ? WHERE id = ?;", request.form.get("phone"), session["user_id"])

        # Update email if submitted
        if request.form.get("email"):
            # Upload email to database
            db.execute("UPDATE users SET email = ? WHERE id = ?;", request.form.get("email"), session["user_id"])

        # Update email if submitted
        if request.form.get("curr"):
            # Upload email to database
            db.execute("UPDATE users SET currency = ? WHERE id = ?;", request.form.get("curr"), session["user_id"])

        # Redirect user to home page
        return redirect("/profile")

    else:
        userprofile = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        return render_template("profile.html", userprofile=userprofile[0], username=session["username"])

@app.route("/updates")
@login_required
def updates():
    return render_template("updates.html", username=session["username"])

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", username=session["username"])

@app.route("/strategies")
@login_required
def strategies():
    reg = re.compile('^crypto_trades')
    evs = []
    if dev:
        tables = db.execute("SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name;")
        for x in tables:
            if reg.match(x['name']):
                evs.append(x['name'])
    else:
        tables = db.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
        for x in tables:
            if reg.match(x['table_name']):
                evs.append(x['table_name'])

    return render_template("strategies.html", evs=evs, username=session["username"])

@app.route("/strategy/<evnum>")
@login_required
def strategy(evnum):
    reg = re.compile('^crypto_trades')
    evs = []
    if dev:
        tables = db.execute("SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name;")
        for x in tables:
            if reg.match(x['name']):
                evs.append(x['name'])
    else:
        tables = db.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
        for x in tables:
            if reg.match(x['table_name']):
                evs.append(x['table_name'])

    if len(evs) < int(evnum):
        return apology("invalid strategy", 400)
    ev = evs[int(evnum)-1]
    table = db.execute("SELECT * FROM " + ev + ";")

    plots = []
    df = pd.DataFrame(table)

    df.rename(columns={'crypto_id': 'id', 'date_buy': 'tbuy', 'date_sell': 'tsell', 'price_buy': 'pbuy', 'price_sell': 'psell', 'trade_return': 'ret',}, inplace=True)

    temp = df.sort_values(by=['tbuy'])
    xval = [str(i)[:-7] for i in temp.tbuy.tolist()]
    yval =  temp['ret'].cumprod().tolist()
    plots.append([xval, yval, "line" , "Cumulative product of percentage gain over time"])

    temp = df[['id', 'ret']].groupby(['id']).mean()
    temp['ret'] = (temp['ret']-1) * 100
    xval = temp.index.tolist()
    yval = temp.ret.tolist()
    plots.append([xval, yval, "bar", "Average return per trade for each token"])

    temp = df
    xval = temp.reset_index().index.tolist()
    yval = temp.ret.tolist()
    plots.append([xval, yval, "scatter", "Trade against return" , 1])
    
    return render_template("strategy.html", trades=table, plotsdata=plots, username=session["username"])

@app.route("/settings")
@login_required
def settings():
    return render_template("settings.html", username=session["username"])

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure symbol and quantity were submitted
        if not request.form.get("symbol") or not request.form.get("shares"):
            return apology("must provide data", 400)

        symbol = request.form.get("symbol")
        quantity = request.form.get("shares")

        try:
            quantity = int(quantity)
        except:
            return apology("Invalid quantiy", 400)

        # Valid input checking
        if (not isinstance(quantity, int)) or (quantity <= 0):
            return apology("Invalid quantiy", 400)

        #stock = lookup(symbol)
        stock = "NULL"

        if (stock) == None:
            return apology("Invalid symbol", 400)

        # Check if enough inpout from user
        stock_value = stock['price'] * quantity

        # Query for balance
        cash = db.execute("SELECT cash FROM users WHERE id = ? ", session["user_id"])[0]['cash']

        if (cash < stock_value):
            return apology("Not enough funds", 400)

        # Take money from user
        db.execute("UPDATE users SET cash = ? WHERE id = ?;", cash-stock_value,  session["user_id"])

        # Add to trade history
        db.execute("INSERT INTO tradehistory (user_id, symbol, quantity, price, buy_sell) VALUES(?, ?, ?, ?, ?)", session["user_id"], symbol, quantity, stock['price'], 1)

        # Add to users holdings
        existing = db.execute("SELECT * FROM holdings WHERE user_id = ? AND symbol = ?", session["user_id"], symbol)
        if len(existing) == 0:
            db.execute("INSERT INTO holdings (user_id, symbol, quantity) VALUES(?, ?, ?)", session["user_id"], symbol, quantity)
        else:
            db.execute("UPDATE holdings SET quantity = ? WHERE id = ?;", existing[0]['quantity']+quantity,  existing[0]['id'])

        return redirect("/")
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    # Query for history
    history = db.execute("SELECT * FROM tradehistory WHERE user_id = ?", session["user_id"])
    for x in range(len(history)):
        if history[x]['buy_sell'] == 1:
            history[x]['buy_sell'] = "Buy"
        else:
            history[x]['buy_sell'] = "Sell"

    return render_template("history.html", history=history, username=session["username"])

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")



@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # return apology("TODO")
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Ensure password was submitted
        elif not request.form.get("confirmation"):
            return apology("must provide confirmation password", 400)

        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        #ensure password is the same
        if password != confirmation:
            return apology("passwords must match", 400)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        # Ensure username exists and password is correct
        if len(rows) != 0:
            return apology("There is already a user with this username", 400)

        # Upload user to database
        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, generate_password_hash(password))

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")



# @app.route("/profile", methods=["GET", "POST"])
# @login_required
# def profile():
#     """Users Profile """
#     # change password
#     # User reached route via POST (as by submitting a form via POST)
#     if request.method == "POST":

#         # Ensure username was submitted
#         if not request.form.get("old_password"):
#             return apology("must provide old_password", 400)

#         # Ensure password was submitted
#         elif not request.form.get("password"):
#             return apology("must provide password", 400)

#         # Ensure password was submitted
#         elif not request.form.get("confirmation"):
#             return apology("must provide confirmation password", 400)

#         # Set variables
#         old_password = request.form.get("old_password")
#         password = request.form.get("password")
#         confirmation = request.form.get("confirmation")

#         # Query user
#         user = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])

#         # Check old password
#         if not check_password_hash(user[0]["hash"], old_password):
#             return apology("incorrect password", 400)

#         #ensure password is the same
#         if password != confirmation:
#             return apology("passwords must match", 400)

#         # Upload user to database
#         db.execute("UPDATE users SET hash = ? WHERE id = ?;", generate_password_hash(password),  session["user_id"])

#         # Redirect user to home page
#         return redirect("/")

    # # User reached route via GET (as by clicking a link or via redirect)
    # else:
    #     return render_template("profile.html")