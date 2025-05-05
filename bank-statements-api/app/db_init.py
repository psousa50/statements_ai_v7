from app.core.database import Base, engine


def init_db():
    """Initialize the database by creating all tables"""
    # Import all models here to ensure they are registered with SQLAlchemy
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


if __name__ == "__main__":
    init_db()
