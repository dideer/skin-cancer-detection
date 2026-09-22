from app import create_app

app = create_app()

# Auto-create database tables on startup
with app.app_context():
    from app.extensions import db
    db.create_all()