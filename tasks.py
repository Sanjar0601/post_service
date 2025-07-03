from celery_worker import celery_app
from datetime import datetime, timedelta
from db import Session
from models import User

@celery_app.task
def delete_unverified_users():
    with Session() as db:
        threshold = datetime.utcnow() - timedelta(seconds=30)
        users_to_delete = db.query(User).filter(
            User.is_verified == False,
            User.created_at < threshold
        ).all()
        for user in users_to_delete:
            print(f"[Celery] Deleting unverified user: {user.email}")
            db.delete(user)
        db.commit()
