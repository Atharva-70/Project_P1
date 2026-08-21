from datetime import datetime
from config.database import db

class Notification(db.Model):
    __tablename__ = "notifications"

    notification_id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    message = db.Column(
        db.String(255),
        nullable = False
    )

    is_read = db.Column(
        db.Boolean,
        nullable = False,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )