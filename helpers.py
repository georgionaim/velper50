from flask import redirect, render_template, session
import requests
from functools import wraps

def error(message):
    """Render message as an apology to user."""
    return render_template("error.html", message = message)

def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def search_word(word):
    try:
        response = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}").json()
        definitions_result = []
        for part in response:
            for definitions in part["meanings"]:
                for definition in definitions["definitions"]:
                    definitions_result.append(definition["definition"])
    except:
        return "error"
    return definitions_result

def summarize(sentence):

    # Edit this One AI API call using our studio at https://studio.oneai.com/?pipeline=7KKaXc&share=true
    api_key = "183f72e8-bfc6-4d36-ba7e-05a65a463d8a"
    url = "https://api.oneai.com/api/v0/pipeline"
    headers = {
    "api-key": api_key,
    "content-type": "application/json"
    }
    payload = {
    "input": sentence,
    "input_type": "article",
        "output_type": "json",
    "steps": [
        {
        "skill": "summarize"
        }
    ],
    }
    r = requests.post(url, json=payload, headers=headers)
    data = r.json()
    try:
        return data["output"][0]["contents"][0]["utterance"], True
    except:
        error_message = data["message"]
        return error_message, False

def keywords(sentence):
    # Edit this One AI API call using our studio at https://studio.oneai.com/?pipeline=ZgUlTP&share=true
    api_key = "183f72e8-bfc6-4d36-ba7e-05a65a463d8a"
    url = "https://api.oneai.com/api/v0/pipeline"
    headers = {
    "api-key": api_key,
    "content-type": "application/json"
    }
    payload = {
    "input": sentence,
    "input_type": "article",
        "output_type": "json",
    "steps": [
        {
        "skill": "keywords"
        }
    ],
    }

    r = requests.post(url, json=payload, headers=headers)
    data = r.json()
    return data

