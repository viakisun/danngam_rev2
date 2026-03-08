"""M04 DRYING 테스트 (TC01~TC05)."""

import uuid
from datetime import date, datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base
from app.models.drying import DryingFacility, DryingReservation, ReservationStatus
from app.models.user import User, UserRole
from app.schemas.drying import FacilityCreate, ReservationComplete, ReservationCreate
from app.services.drying_service import (
    calculate_yield,
    complete_reservation,
    create_reservation,
    register_facility,
)

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
async def operator(db: AsyncSession) -> User:
    user = User(
        id=uuid.uuid4(),
        phone="01033330003",
        current_role=UserRole.REQUESTER,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.flush()
    return user


@pytest_asyncio.fixture
async def requester(db: AsyncSession) -> User:
    user = User(
        id=uuid.uuid4(),
        phone="01044440004",
        current_role=UserRole.REQUESTER,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.flush()
    return user


@pytest_asyncio.fixture
async def facility(db: AsyncSession, operator: User) -> DryingFacility:
    f = await register_facility(
        db,
        operator.id,
        FacilityCreate(
            name="논산 건조시설",
            location_address="충남 논산시 테스트동",
            location_lat=36.19,
            location_lng=127.09,
            capacity_kg=5000.0,
            price_per_kg=50,
            available_crops=["rice", "barley"],
        ),
    )
    return f


class TestTC01_RegisterFacility:
    """TC01: 시설 등록."""

    async def test_register_facility(self, db, operator):
        facility = await register_facility(
            db,
            operator.id,
            FacilityCreate(
                name="테스트 건조장",
                location_address="충남 논산시",
                location_lat=36.19,
                location_lng=127.09,
                capacity_kg=3000.0,
                price_per_kg=40,
            ),
        )
        assert facility.id is not None
        assert facility.name == "테스트 건조장"
        assert facility.operator_id == operator.id
        assert facility.is_active is True


class TestTC02_CreateReservation:
    """TC02: 예약 생성."""

    async def test_create_reservation(self, db, requester, facility):
        reservation = await create_reservation(
            db,
            requester.id,
            ReservationCreate(
                facility_id=facility.id,
                crop_type="rice",
                input_kg=1000.0,
                scheduled_date=date(2026, 9, 20),
            ),
        )
        assert reservation.id is not None
        assert reservation.status == ReservationStatus.PENDING
        assert reservation.input_kg == 1000.0
        assert reservation.output_kg is None
        assert reservation.yield_pct is None


class TestTC03_CompleteWithYield:
    """TC03: 건조 완료 + 수율 계산."""

    async def test_complete_reservation_yield(self, db, requester, facility):
        reservation = await create_reservation(
            db,
            requester.id,
            ReservationCreate(
                facility_id=facility.id,
                crop_type="rice",
                input_kg=1000.0,
                scheduled_date=date(2026, 9, 21),
            ),
        )
        completed = await complete_reservation(
            db,
            reservation.id,
            facility.operator_id,
            ReservationComplete(
                output_kg=850.0,
                moisture_pct=14.5,
                color_grade="A",
                quality_grade="1등급",
            ),
        )
        assert completed.status == ReservationStatus.COMPLETED
        assert completed.output_kg == 850.0
        assert completed.yield_pct == 85.0  # 850/1000*100
        assert completed.moisture_pct == 14.5
        assert completed.color_grade == "A"
        assert completed.quality_grade == "1등급"


class TestTC04_YieldAccuracy:
    """TC04: 수율 계산 정확도."""

    def test_yield_calculation_exact(self):
        assert calculate_yield(1000.0, 850.0) == 85.0

    def test_yield_calculation_rounding(self):
        # 1/3 → 33.33%
        result = calculate_yield(300.0, 100.0)
        assert result == pytest.approx(33.33, abs=0.01)

    def test_yield_full_output(self):
        assert calculate_yield(1000.0, 1000.0) == 100.0

    def test_yield_partial(self):
        assert calculate_yield(500.0, 250.0) == 50.0


class TestTC05_OutputExceedsInput:
    """TC05: output_kg > input_kg → 에러."""

    def test_output_exceeds_input_raises(self):
        with pytest.raises(ValueError, match="DNNG-DRY-003"):
            calculate_yield(1000.0, 1001.0)

    async def test_complete_with_excess_output(self, db, requester, facility):
        reservation = await create_reservation(
            db,
            requester.id,
            ReservationCreate(
                facility_id=facility.id,
                crop_type="rice",
                input_kg=500.0,
                scheduled_date=date(2026, 9, 22),
            ),
        )
        with pytest.raises(ValueError, match="DNNG-DRY-003"):
            await complete_reservation(
                db,
                reservation.id,
                facility.operator_id,
                ReservationComplete(output_kg=600.0),
            )
