from celery import Celery

def create_celery():
    celery = Celery('flaskapp')
    celery.config_from_object('flaskapp.celeryconfig')
    return celery

celery = create_celery()
