# blocklist.py

from datetime import datetime
from models import TokenBlocklist
from db import db

def add_to_blocklist(jti):
    """Add a JWT token's jti to the blocklist if it isn't already there."""
    # Check if the token's jti is already in the blocklist
    if not TokenBlocklist.query.filter_by(jti=jti).first():
        blocked_token = TokenBlocklist(jti=jti)
        db.session.add(blocked_token)
        db.session.commit()
    else:
        print(f"Token with jti {jti} is already in the blocklist.")

def remove_from_blocklist(jti):
    """Remove a JWT token's jti from the blocklist."""
    blocked_token = TokenBlocklist.query.filter_by(jti=jti).first()
    if blocked_token:
        db.session.delete(blocked_token)
        db.session.commit()

def is_token_blocked(jti):
    """Check if a JWT token's jti is in the blocklist."""
    token = TokenBlocklist.query.filter_by(jti=jti).first()
    if token:
        print(f"Token with jti {jti} is found in blocklist.")  # Debugging line
    else:
        print(f"Token with jti {jti} is NOT found in blocklist.")  # Debugging line
    return token is not None