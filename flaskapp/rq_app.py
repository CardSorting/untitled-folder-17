import os
from flask import Flask
from redis import Redis
from rq import Queue

def create_rq():
    flask_app = Flask(__name__)
    flask_app.config.from_object(os.environ.get('FLASK_CONFIG', 'flaskapp.config.Config'))

    redis_url = flask_app.config['REDIS_URL']
    redis_conn = Redis.from_url(redis_url, ssl_cert_reqs=None)
    
    q = Queue(connection=redis_conn)

    with flask_app.app_context():
        return q

q = create_rq()
