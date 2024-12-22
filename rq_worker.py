import os
from dotenv import load_dotenv
from redis import Redis
from rq import Worker, Queue

load_dotenv()

if __name__ == '__main__':
    redis_url = os.environ.get('REDIS_URL')
    redis_conn = Redis.from_url(redis_url, ssl_cert_reqs=None)
    q = Queue(connection=redis_conn)
    
    worker = Worker([q], connection=redis_conn)
    worker.work()
