from flask import Flask, request
from scraper import extract

app = Flask(__name__)

@app.get('/')
def index():
    query = request.args.get('query')
    result = extract(query, 10)

    return result