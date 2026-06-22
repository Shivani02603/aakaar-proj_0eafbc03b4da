from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('sessions.id'), nullable=False)
    created_at = Column(DateTime, nullable=False)

class Session(Base):
    __tablename__ = 'sessions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

class UploadedFile(Base):
    __tablename__ = 'uploaded_files'
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('sessions.id'), nullable=False)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_size = Column(Float, nullable=False)
    content_type = Column(String, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)

class DocumentChunk(Base):
    __tablename__ = 'document_chunks'
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(Integer, ForeignKey('uploaded_files.id'), nullable=False)
    session_id = Column(Integer, ForeignKey('sessions.id'), nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Text, nullable=True)
    metadata = Column(Text, nullable=True)
    chunk_index = Column(Integer, nullable=False)
    token_count = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False)

class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('sessions.id'), nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    metadata = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False)