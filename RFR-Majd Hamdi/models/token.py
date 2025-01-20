from db import db
from datetime import datetime

class TokenBlocklist(db.Model):
    __tablename__ = 'token_blocklist'

    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(255), unique=True, nullable=False)
    revoked_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, jti, revoked_at=None):
        self.jti = jti
        if revoked_at:
            self.revoked_at = revoked_at
