from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

# Create SQLAlchemy engine
print("Database URL:", settings.DATABASE_URL)  # Debugging line to check database URL
engine = create_engine(settings.DATABASE_URL)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()

# This function is kept for backward compatibility and testing
# but is not used in the main application flow anymore
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
