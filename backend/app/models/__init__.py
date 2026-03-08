# 모든 모델을 여기서 임포트 (Alembic autogenerate 지원)
from app.models.chat import ChatMessage, ChatRoom  # noqa: F401
from app.models.drying import DryingFacility, DryingReservation  # noqa: F401
from app.models.job import Job, JobApplication  # noqa: F401
from app.models.notification import FCMToken, Notification  # noqa: F401
from app.models.payment import Payment  # noqa: F401
from app.models.review import Review  # noqa: F401
from app.models.user import User  # noqa: F401
