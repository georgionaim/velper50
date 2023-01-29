# Libraries
from cs50 import SQL
from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
import helpers

# Configure app
app = Flask(__name__)

# Auto-reload templates
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

#Connect to the vocab.db database
db = SQL("sqlite:///vocab.db")

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        username = request.form.get("username").lower()
        password = request.form.get("password")
        # Ensure username was submitted
        if not username:
            return helpers.error("must provide username")

        # Ensure password was submitted
        elif not password:
            return helpers.error("must provide password")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            return helpers.error("invalid username and/or password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session["user_first_entry"] = False
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

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # If enter via post
    if request.method == "POST":

        # Extract the form fields (username, password)
        username = request.form.get("username").lower()
        password = request.form.get("password")

        if len(password) == 0 or len(username) == 0 :
            return helpers.error("Must fill all field")

        # Check if the name already exist in database or Blank field
        same_names = db.execute("SELECT COUNT(*) as count FROM users WHERE username = ?;", username)[0]["count"]
        if same_names != 0:
            return helpers.error("Name Already taken")

        # If no errors, first hash the password for security, then add the user into database, and finally let the user in
        else:
            hash_password = generate_password_hash(password)
            db.execute("INSERT INTO users(username, hash) VALUES(?,?);",username, hash_password)
            person_id = db.execute("SELECT id FROM users WHERE username = ?", username)[0]["id"]
            session["user_id"] = person_id
            session["user_first_entry"] = True
            return redirect("/")

    # If enter via get
    else:
        session.clear()
        return render_template("register.html")

@app.route("/finished_greet", methods=["POST"])
@helpers.login_required
def greet_finished():
    session["user_first_entry"] = False
    return redirect("/")

input()
@app.route("/", methods=["GET"])
@helpers.login_required
def index():
    greet_entry = False
    if session["user_first_entry"] == True:
        greet_entry = True
    user_id = session["user_id"]
    dictionary = db.execute("SELECT word, definition from vocab WHERE user_id = ?", user_id)
    name = db.execute("SELECT username from users WHERE id = ?", user_id)[0]["username"]
    return render_template("index.html", dictionary = dictionary, home=True, len_dict = len(dictionary), greet_entry = greet_entry, name = name)


@app.route("/add",methods = ["GET", "POST"])
@helpers.login_required
def add():
    user_id = session["user_id"]
    if request.method == "POST":
        word = request.form.get("word").lower()
        definition = request.form.get("definition")

        if len(word) == 0 or len(definition) == 0:
            return helpers.error("Must fill all fields")

        if ' ' in word:
            return helpers.error("Your word must not have any whitespace in it please fill the blank space with _ or check if you unaccidently type whitespace in the end of the word")

        rows = db.execute("SELECT COUNT(*) as count FROM vocab WHERE user_id = ? AND word = ?", user_id, word)[0]["count"]
        if rows != 0:
            return helpers.error("Word already in table.")
        else:
            db.execute("INSERT INTO vocab VALUES(?, ?, ?)",user_id, word, definition)
            return redirect("/")
    else:
        return render_template("add.html", home=True)


@app.route("/search", methods = ["GET", "POST"])
@helpers.login_required
def search():
    if request.method == "POST":
        word = request.form.get("word")
        all_definitions = helpers.search_word(word)
        if all_definitions == "error":
            return helpers.error("No definition found, please check the word spell and try again")
        definitions = []
        for counter,definition in enumerate(all_definitions):
            definitions.append(definition)
            if counter == 9:
                break
        definitions = dict(list(enumerate(definitions)))
        return render_template("search_result.html", definitions = definitions, home=True, word = word)
    else:
        return render_template("search.html", home=True)

@app.route("/save_def", methods=["POST"])
@helpers.login_required
def save_def():
    user_id = session["user_id"]
    word = request.form.get("word").lower()
    def_number = request.form.get("definition_number")
    if def_number == None:
        return helpers.error("Must provide a number")
    rows = db.execute("SELECT COUNT(*) as count from vocab WHERE user_id = ? AND word = ?", user_id, word)[0]["count"]
    if rows != 0:
        return helpers.error("Word already in table")
    def_number = int(def_number) - 1
    definition = helpers.search_word(word)[def_number]

    word = word.replace(" ", "_")
    db.execute("INSERT INTO vocab(user_id, word, definition) values(?,?,?)", user_id, word, definition)
    return redirect("/")



@app.route("/remove", methods = ["GET", "POST"])
@helpers.login_required
def remove():
    user_id = session["user_id"]
    if request.method == "POST":
        word = request.form.get("word")
        definition = db.execute("SELECT definition FROM vocab WHERE user_id = ? AND word = ?", user_id, word)
        rows = db.execute("SELECT COUNT(*) as count FROM vocab WHERE user_id = ? AND word = ?", user_id, word)[0]["count"]
        if rows == 0:
            return helpers.error("Word don't exist in table")
        db.execute("DELETE FROM vocab WHERE user_id = ? AND word = ?",user_id, word)
        db.execute("DELETE FROM saver WHERE user_id = ? AND word = ?", user_id, word)
        db.execute("INSERT INTO history(user_id, word, definition) VALUES(?,?,?)", user_id, word, definition[0]["definition"])
        return redirect("/")
    else:
        words = db.execute("SELECT word FROM vocab WHERE user_id = ?", user_id)
        return render_template("remove.html", home=True, words=words)

@app.route("/edit", methods = ["GET", "POST"])
@helpers.login_required
def edit():
    user_id = session["user_id"]
    if request.method == "POST":
        word = request.form.get("word")
        new_definition = request.form.get("new_definition")
        if word == None or len(new_definition) == 0:
            return helpers.error("Must fill all fields")

        rows = db.execute("SELECT COUNT(*) as count FROM vocab WHERE user_id = ? AND word = ?", user_id, word)[0]["count"]
        if rows == 0:
            return helpers.error("Word not found in table.")
        db.execute("UPDATE vocab set definition = ? WHERE user_id = ? AND word = ? ",new_definition, user_id, word)
        saves = db.execute("SELECT word FROM saver WHERE user_id = ? AND word = ?", user_id, word)
        if len(saves) != 0:
            db.execute("DELETE FROM saver WHERE user_id = ? AND word = ?", user_id, word)
        return redirect("/")

    else:
        words = db.execute("SELECT word FROM vocab WHERE user_id = ?", user_id)
        return render_template("edit.html", home=True, words = words)


@app.route("/archive", methods = ["GET"])
@helpers.login_required
def archive():
    user_id = session["user_id"]
    dictionary = db.execute("SELECT * FROM history where user_id = ?", user_id)
    return render_template("archive.html", dictionary = dictionary, len_hist = len(dictionary))


@app.route("/recover", methods = ["POST"])
@helpers.login_required
def recover_history():
    user_id = session["user_id"]
    word = request.form.get("word")
    definition = request.form.get("definition")
    rows = db.execute("SELECT COUNT(*) as count from vocab where user_id = ? and word = ?", user_id, word)[0]["count"]
    if rows != 0:
        return helpers.error("Word already in table")
    db.execute("INSERT INTO vocab(user_id, word, definition) VALUES(?, ?, ?)", user_id, word, definition)
    db.execute("DELETE FROM history WHERE word = ? AND user_id = ?", word, user_id)
    return redirect("/")

@app.route("/delete", methods = ["POST"])
@helpers.login_required
def delete_history():
    user_id = session["user_id"]
    word = request.form.get("word")
    db.execute("DELETE FROM history WHERE user_id = ? AND word = ?", user_id, word)
    return redirect("/archive")

@app.route("/about", methods = ["POST", "GET"])
def about():
    if request.method == "POST":
        return redirect("/")
    else:
        return render_template("about.html")

@app.route("/summarize", methods = ["POST", "GET"])
@helpers.login_required
def summarize():
    user_id = session["user_id"]
    same = False
    if request.method == "POST":
        word = request.form.get("word")
        definition = db.execute("SELECT definition from vocab where user_id = ? AND word = ?", user_id, word)
        if len(definition) == 0:
            return helpers.error("Word not found in table.")
        sentence = helpers.summarize(definition[0]["definition"])
        if not sentence[1]:
            return helpers.error(sentence[0])
        if sentence == definition:
            same = True
        return render_template("summarize_result.html", sentence=sentence[0],word = word, help = True, same = same)
    else:
        words = db.execute("SELECT word FROM vocab WHERE user_id = ?", user_id)
        return render_template("summarize.html", help = True, words = words)

@app.route("/saver", methods = ["GET"])
@helpers.login_required
def saver():
    user_id = session["user_id"]
    rows = db.execute("SELECT * FROM saver WHERE user_id = ?", user_id)
    return render_template("saves.html", rows = rows, len_sv = len(rows))

@app.route("/save", methods = ["POST"])
@helpers.login_required
def save_help():
    user_id = session["user_id"]
    type = request.form.get("type")
    word = request.form.get("word")
    result = request.form.get("result")
    if word == None:
        return helpers.error("Must provide a word")
    if type == "description":
        description_word = db.execute("SELECT word from saver WHERE user_id = ? AND type = ?", user_id, "description")
        for i in description_word:
            if i["word"] == word:
                db.execute("UPDATE saver SET result = ? WHERE user_id = ? AND type = ? AND word = ?", result, user_id, "description", word)
                return redirect("/saver")

    db.execute("INSERT INTO saver(user_id, type,  word, result) VALUES(?,?,?,?)", user_id, type, word, result)
    return redirect("/saver")


@app.route("/completed", methods = ["POST"])
@helpers.login_required
def completed():
    user_id = session["user_id"]
    word = request.form.get("word")
    type = request.form.get("type")
    db.execute("DELETE FROM saver WHERE user_id = ? AND word = ? AND type = ?", user_id, word, type)
    return redirect("/saver")

@app.route("/keywords", methods = ["GET", "POST"])
@helpers.login_required
def keywords():
    keys = set()
    user_id = session["user_id"]
    if request.method == "POST":
        word = request.form.get("word")
        if word == None:
            return helpers.error("Must Provide a word")

        definition = db.execute("SELECT definition FROM vocab WHERE user_id = ? AND word = ?", user_id, word)[0]["definition"]
        keywords = helpers.keywords(definition)
        for i in keywords["output"][0]["labels"]:
            keys.add(i["name"])
        if len(keys) == 0:
            keys = None
        return render_template("keywords_result.html", keywords = keys, help=True, word = word)
    else:
        words = db.execute("SELECT word FROM vocab WHERE user_id = ?", user_id)
        return render_template("keyword.html", words=words, help=True)


@app.route("/description", methods = ["GET"])
@helpers.login_required
def description():
    user_id = session["user_id"]
    words = db.execute("SELECT word FROM vocab WHERE user_id = ?", user_id)
    return render_template("description.html", help=True, words = words)
