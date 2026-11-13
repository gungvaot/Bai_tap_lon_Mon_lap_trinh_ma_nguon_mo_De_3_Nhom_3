import os

os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["SECRET_KEY"] = "test-secret"
if os.path.exists("test.db"):
    os.remove("test.db")