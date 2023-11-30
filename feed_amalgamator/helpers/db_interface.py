"""Abstraction layer for connecting to the database.
This allows for easier manipulation of the data. More importantly, it allows the program to work
with any SQL backend, be it PostGRE or MySQl."""
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


db = SQLAlchemy()  # Not initialized without the app


class User(db.Model):
    __tablename__ = "users"
    user_id: Mapped[int] = mapped_column(db.Integer, primary_key=True)  # table index
    username: Mapped[str] = mapped_column(db.String, nullable=False)
    hashed_password: Mapped[str] = mapped_column(db.String, nullable=False)
    salt: Mapped[int] = mapped_column(db.Integer, nullable=False)


class UserServers(db.Model):
    __tablename__ = "user_servers"
    user_server_id: Mapped[int] = mapped_column(db.Integer, primary_key=True)  # table index
    user_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey("users.user_id"))
    server_url: Mapped[str] = mapped_column(db.String, nullable=False)
    """TODO - For future versions of the project. The access token to the third party api is stored as plaintext
    at the moment. Coming up with a solution is not viable for this sprint"""
    oauth: Mapped[str] = mapped_column(db.String(80), nullable=False)
