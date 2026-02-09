from sqlalchemy.orm import Session
from models.orm import MessageORM
from models.schemas import MessageCreate
import uuid
import time

def save_message_repo(
    db: Session,
    message_data: MessageCreate,
    sender_type: str,
    sender_id: str | None = None
) -> MessageORM:
    new_msg = MessageORM(
        id=str(uuid.uuid4()),
        group_id=message_data.group_id,
        sender_id=sender_id or message_data.sender_id,
        sender_type=sender_type,
        text=message_data.content,
        timestamp=time.time(),
    )
    db.add(new_msg)
    db.commit()
    db.refresh(new_msg)
    return new_msg

def list_group_messages_repo(db: Session, group_id: str) -> list[MessageORM]:
    return (
        db.query(MessageORM)
        .filter(MessageORM.group_id == group_id)
        .order_by(MessageORM.timestamp.asc())
        .all()
    )

def get_message_repo(db: Session, message_id: str) -> MessageORM | None:
    return db.query(MessageORM).filter(MessageORM.id == message_id).first()

def delete_message_repo(db: Session, message_id: str) -> bool:
    msg = get_message_repo(db, message_id)
    if not msg:
        return False
    db.delete(msg)
    db.commit()
    return True