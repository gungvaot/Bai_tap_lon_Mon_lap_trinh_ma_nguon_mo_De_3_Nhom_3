import os

os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["SECRET_KEY"] = "test-secret"
os.environ["UPLOAD_DIR"] = "test_uploads"
if os.path.exists("test.db"):
    os.remove("test.db")

from app import models  # noqa: E402, F401
from app.database import Base, engine  # noqa: E402

Base.metadata.create_all(engine)