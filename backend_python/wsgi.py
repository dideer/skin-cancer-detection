from app import create_app

app = create_app()

# Auto-create database tables on startup (non-blocking)
with app.app_context():
    try:
        from app.extensions import db
        db.create_all()
    except Exception as e:
        print(f"⚠️  Warning: Could not create tables: {e}")
        # Continue anyway - DB may not be ready yet