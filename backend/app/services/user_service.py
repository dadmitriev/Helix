from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import hash_password
from app.models.patient import Gender, Patient
from app.models.user import User, UserRole
from app.repositories.patient_repository import PatientRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = UserRepository(session)
        self.patient_repo = PatientRepository(session)

    async def create(self, data: UserCreate) -> User:
        if await self.repo.email_exists(data.email):
            raise ConflictError(f"Email '{data.email}' is already registered")

        user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            role=data.role,
            first_name=data.first_name,
            last_name=data.last_name,
            middle_name=data.middle_name,
        )
        user = await self.repo.create(user)

        if data.role == UserRole.PATIENT:
            mrn = await self.patient_repo.generate_mrn()
            patient = Patient(
                user_id=user.id,
                created_by=user.id,
                medical_record_number=mrn,
                first_name=data.first_name,
                last_name=data.last_name,
                middle_name=data.middle_name,
                date_of_birth=data.date_of_birth or date(1990, 1, 1),
                gender=data.gender or Gender.MALE,
                family_history_diabetes=False,
            )
            self.patient_repo.session.add(patient)
            await self.patient_repo.session.flush()

        return user

    async def get_or_404(self, user_id: UUID) -> User:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        return user

    async def update(self, user_id: UUID, data: UserUpdate) -> User:
        user = await self.get_or_404(user_id)
        if data.email and data.email != user.email:
            if await self.repo.email_exists(data.email, exclude_id=user_id):
                raise ConflictError(f"Email '{data.email}' is already taken")
            user.email = data.email
        if data.first_name is not None:
            user.first_name = data.first_name
        if data.last_name is not None:
            user.last_name = data.last_name
        if data.middle_name is not None:
            user.middle_name = data.middle_name
        await self.repo.flush()
        return user

    async def toggle_active(self, user_id: UUID) -> User:
        user = await self.get_or_404(user_id)
        user.is_active = not user.is_active
        await self.repo.flush()
        return user

    async def list_users(
        self,
        role: UserRole | None = None,
        is_active: bool | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[User], int]:
        return await self.repo.list_filtered(role, is_active, offset, limit)

    async def list_doctors(self) -> list[User]:
        doctors, _ = await self.repo.get_by_role(UserRole.DOCTOR, limit=500)
        return doctors
