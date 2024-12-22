from flaskapp.celery_app import celery

if __name__ == '__main__':
    celery.worker_main(['worker', '--loglevel=info', '--pool=solo'])
