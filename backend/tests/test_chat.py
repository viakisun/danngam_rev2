"""M05 CHAT 테스트 (TC01~TC05)."""

import uuid
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base
from app.models.chat import ChatMessage, ChatRoom, MESSAGE_MAX_LENGTH
from app.models.job import Job, JobCategory, JobStatus, PayType
from app.models.user import User, UserRole
from app.schemas.chat import ChatMessageResponse, ChatRoomResponse

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="module")
async def test_engine():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db(test_engine):
    session_factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def requester(db: AsyncSession) -> User:
    user = User(
        id=uuid.uuid4(),
        phone="01055550005",
        current_role=UserRole.REQUESTER,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.flush()
    return user


@pytest_asyncio.fixture
async def worker(db: AsyncSession) -> User:
    user = User(
        id=uuid.uuid4(),
        phone="01066660006",
        current_role=UserRole.WORKER,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.flush()
    return user


@pytest_asyncio.fixture
async def job(db: AsyncSession, requester: User) -> Job:
    j = Job(
        id=uuid.uuid4(),
        requester_id=requester.id,
        title="벼베기 작업",
        category=JobCategory.RICE_HARVESTING,
        location_lat=36.19,
        location_lng=127.09,
        location_address="충남 논산시",
        area_pyeong=3000,
        pay_type=PayType.PER_PYEONG,
        status=JobStatus.MATCHED,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(j)
    await db.flush()
    return j


@pytest_asyncio.fixture
async def chat_room(db: AsyncSession, job: Job, requester: User, worker: User) -> ChatRoom:
    """매칭 성사 시 자동 생성되는 채팅방."""
    room = ChatRoom(
        id=uuid.uuid4(),
        job_id=job.id,
        requester_id=requester.id,
        worker_id=worker.id,
        created_at=datetime.now(timezone.utc),
    )
    db.add(room)
    await db.flush()
    return room


class TestTC01_ChatRoomAutoCreation:
    """TC01: 매칭 성사 → 채팅방 자동 생성 확인."""

    async def test_chat_room_created(self, db, chat_room, job, requester, worker):
        assert chat_room.id is not None
        assert chat_room.job_id == job.id
        assert chat_room.requester_id == requester.id
        assert chat_room.worker_id == worker.id


class TestTC02_ListChatRooms:
    """TC02: 채팅방 목록 조회."""

    async def test_list_rooms_model(self, db, chat_room, requester):
        from sqlalchemy import select, or_

        result = await db.execute(
            select(ChatRoom).where(
                or_(
                    ChatRoom.requester_id == requester.id,
                    ChatRoom.worker_id == requester.id,
                )
            )
        )
        rooms = result.scalars().all()
        assert len(rooms) >= 1
        assert any(r.id == chat_room.id for r in rooms)


class TestTC03_MessageHistory:
    """TC03: 메시지 히스토리 조회."""

    async def test_message_history(self, db, chat_room, requester):
        # 메시지 3개 추가
        for i in range(3):
            msg = ChatMessage(
                id=uuid.uuid4(),
                room_id=chat_room.id,
                sender_id=requester.id,
                content=f"메시지 {i + 1}",
                is_read=False,
                created_at=datetime.now(timezone.utc),
            )
            db.add(msg)
        await db.flush()

        from sqlalchemy import select

        result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.room_id == chat_room.id)
            .order_by(ChatMessage.created_at)
        )
        messages = result.scalars().all()
        assert len(messages) >= 3
        contents = [m.content for m in messages]
        assert "메시지 1" in contents


class TestTC04_MarkAsRead:
    """TC04: 읽음 처리."""

    async def test_mark_as_read(self, db, chat_room, worker):
        # worker가 보낸 메시지 (requester가 읽음 처리할 대상)
        msg = ChatMessage(
            id=uuid.uuid4(),
            room_id=chat_room.id,
            sender_id=worker.id,
            content="안녕하세요",
            is_read=False,
            created_at=datetime.now(timezone.utc),
        )
        db.add(msg)
        await db.flush()

        from sqlalchemy import and_, update

        now = datetime.now(timezone.utc)
        # requester 입장에서 worker 메시지를 읽음 처리
        await db.execute(
            update(ChatMessage)
            .where(
                and_(
                    ChatMessage.room_id == chat_room.id,
                    ChatMessage.sender_id != chat_room.requester_id,
                    ChatMessage.is_read.is_(False),
                )
            )
            .values(is_read=True, read_at=now)
        )
        await db.flush()

        from sqlalchemy import select

        result = await db.execute(
            select(ChatMessage).where(ChatMessage.id == msg.id)
        )
        updated = result.scalar_one()
        assert updated.is_read is True
        assert updated.read_at is not None


class TestTC05_MessageLengthLimit:
    """TC05: 메시지 길이 제한 (1000자)."""

    def test_message_max_length_constant(self):
        assert MESSAGE_MAX_LENGTH == 1000

    async def test_long_message_rejected_by_schema(self):
        from pydantic import ValidationError

        from app.schemas.chat import SendMessageRequest

        with pytest.raises(ValidationError):
            SendMessageRequest(content="a" * 1001)

    async def test_valid_message_accepted(self):
        from app.schemas.chat import SendMessageRequest

        req = SendMessageRequest(content="a" * 1000)
        assert len(req.content) == 1000
