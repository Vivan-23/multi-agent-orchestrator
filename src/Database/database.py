import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Load env file
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:vivan91362@localhost:5432/recon_db")

# Automatically switch to host.docker.internal if running inside docker and database is on localhost
is_in_docker = os.path.exists('/.dockerenv')
if not is_in_docker and os.path.exists('/proc/1/cgroup'):
    try:
        with open('/proc/1/cgroup', 'r', errors='ignore') as f:
            if any('docker' in line for line in f):
                is_in_docker = True
    except Exception:
        pass

if is_in_docker:
    if "localhost" in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("localhost", "host.docker.internal")
    elif "127.0.0.1" in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("127.0.0.1", "host.docker.internal")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
