import os
import uuid
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from database.models import (
    engine,
    SessionLocal,
    User,
    Session,
    UploadedFile,
    DocumentChunk,
    Message,
)

def seed_database():
    session = SessionLocal()
    try:
        # Clear existing data
        session.query(Message).delete()
        session.query(DocumentChunk).delete()
        session.query(UploadedFile).delete()
        session.query(Session).delete()
        session.query(User).delete()

        # Seed Users
        user1 = User(id=uuid.uuid4(), session_id="session_1", created_at=datetime.utcnow())
        user2 = User(id=uuid.uuid4(), session_id="session_2", created_at=datetime.utcnow())
        user3 = User(id=uuid.uuid4(), session_id="session_3", created_at=datetime.utcnow())
        session.add_all([user1, user2, user3])
        session.flush()  # Flush to generate IDs for FK references

        # Seed Sessions
        session1 = Session(
            id=uuid.uuid4(),
            user_id=user1.id,
            name="Session 1",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session2 = Session(
            id=uuid.uuid4(),
            user_id=user2.id,
            name="Session 2",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session3 = Session(
            id=uuid.uuid4(),
            user_id=user3.id,
            name="Session 3",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add_all([session1, session2, session3])
        session.flush()

        # Seed UploadedFiles
        file1 = UploadedFile(
            id=uuid.uuid4(),
            session_id=session1.id,
            filename="file1.txt",
            original_filename="original_file1.txt",
            file_size=1024,
            content_type="text/plain",
            status="processed",
            created_at=datetime.utcnow(),
        )
        file2 = UploadedFile(
            id=uuid.uuid4(),
            session_id=session2.id,
            filename="file2.txt",
            original_filename="original_file2.txt",
            file_size=2048,
            content_type="text/plain",
            status="processed",
            created_at=datetime.utcnow(),
        )
        file3 = UploadedFile(
            id=uuid.uuid4(),
            session_id=session3.id,
            filename="file3.txt",
            original_filename="original_file3.txt",
            file_size=4096,
            content_type="text/plain",
            status="processed",
            created_at=datetime.utcnow(),
        )
        session.add_all([file1, file2, file3])
        session.flush()

        # Seed DocumentChunks
        chunk1 = DocumentChunk(
            id=uuid.uuid4(),
            file_id=file1.id,
            session_id=session1.id,
            content="This is the content of chunk 1.",
            embedding=[0.1] * 1536,
            metadata={"source": "file1"},
            chunk_index=0,
            token_count=50,
            created_at=datetime.utcnow(),
        )
        chunk2 = DocumentChunk(
            id=uuid.uuid4(),
            file_id=file2.id,
            session_id=session2.id,
            content="This is the content of chunk 2.",
            embedding=[0.2] * 1536,
            metadata={"source": "file2"},
            chunk_index=1,
            token_count=60,
            created_at=datetime.utcnow(),
        )
        chunk3 = DocumentChunk(
            id=uuid.uuid4(),
            file_id=file3.id,
            session_id=session3.id,
            content="This is the content of chunk 3.",
            embedding=[0.3] * 1536,
            metadata={"source": "file3"},
            chunk_index=2,
            token_count=70,
            created_at=datetime.utcnow(),
        )
        session.add_all([chunk1, chunk2, chunk3])
        session.flush()

        # Seed Messages
        message1 = Message(
            id=uuid.uuid4(),
            session_id=session1.id,
            role="user",
            content="Hello, assistant!",
            metadata={"intent": "greeting"},
            created_at=datetime.utcnow(),
        )
        message2 = Message(
            id=uuid.uuid4(),
            session_id=session2.id,
            role="assistant",
            content="Hello, user!",
            metadata={"response": "greeting"},
            created_at=datetime.utcnow(),
        )
        message3 = Message(
            id=uuid.uuid4(),
            session_id=session3.id,
            role="system",
            content="System initialized.",
            metadata={"status": "init"},
            created_at=datetime.utcnow(),
        )
        session.add_all([message1, message2, message3])

        # Commit the transaction
        session.commit()
        print("Database seeded successfully!")
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Error seeding database: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    seed_database()