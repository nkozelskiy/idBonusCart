from sqlalchemy import Column, Integer, String
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    password_hash = Column(String(256), nullable=False)

    # Роли: "employee" — сотрудник, "admin" — администратор
    role = Column(String(16), nullable=False, default="employee")
