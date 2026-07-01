from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.patient import Patient
from app.models.user import User, UserRole
from app.repositories.patient_repository import PatientRepository
from app.schemas.patient import PatientCreate, PatientUpdate


class PatientService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = PatientRepository(session)

    async def create(self, data: PatientCreate, created_by: User) -> Patient:
        mrn = await self.repo.generate_mrn()

        patient = Patient(
            first_name=data.first_name,
            last_name=data.last_name,
            middle_name=data.middle_name,
            date_of_birth=data.date_of_birth,
            gender=data.gender,
            phone=data.phone,
            address=data.address,
            family_history_diabetes=data.family_history_diabetes,
            medical_record_number=mrn,
            created_by=created_by.id,
            user_id=data.user_id,
        )
        return await self.repo.create(patient)

    async def get_or_404(self, patient_id: UUID) -> Patient:
        patient = await self.repo.get_by_id_with_relations(patient_id)
        if not patient:
            raise NotFoundError(f"Patient {patient_id} not found")
        return patient

    async def get_for_current_user(self, user: User) -> Patient:
        """Resolve the patient card linked to the current PATIENT-role user."""
        patient = await self.repo.get_by_user_id(user.id)
        if not patient:
            raise NotFoundError("No patient card linked to your account")
        return patient

    async def check_access(self, patient: Patient, user: User) -> None:
        """Raise ForbiddenError if user has no right to view this patient."""
        if user.role == UserRole.PATIENT:
            linked = await self.repo.get_by_user_id(user.id)
            if not linked or linked.id != patient.id:
                raise ForbiddenError("You can only view your own patient record")

    async def update(self, patient_id: UUID, data: PatientUpdate) -> Patient:
        patient = await self.get_or_404(patient_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(patient, field, value)
        await self.repo.flush()
        return patient

    async def search(
        self, query: str | None, offset: int, limit: int
    ) -> tuple[list[Patient], int]:
        return await self.repo.search(query, offset, limit)
