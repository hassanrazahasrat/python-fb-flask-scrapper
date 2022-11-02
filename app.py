from flask import Flask, request
from scraper import extract

app = Flask(__name__, static_url_path='', static_folder='static')

@app.get('/')
def index():
    query = request.args.get('query')
    result = extract(query, 8)

    return result

@app.get('/q/<query>')
def indexQuery(query):
    try:
        limit = int(request.args.get('num_posts', 8))
    except ValueError:
        limit = 8

    result = extract(query, limit)

    return result
