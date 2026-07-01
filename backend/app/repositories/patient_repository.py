from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.patient import Patient
from app.repositories.base import BaseRepository


class PatientRepository(BaseRepository[Patient]):
    model = Patient

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_id_with_relations(self, patient_id: UUID) -> Patient | None:
        q = (
            select(Patient)
            .where(Patient.id == patient_id)
            .options(
                selectinload(Patient.user),
                selectinload(Patient.creator),
            )
        )
        return (await self.session.execute(q)).scalar_one_or_none()

    async def get_by_mrn(self, mrn: str) -> Patient | None:
        q = select(Patient).where(Patient.medical_record_number == mrn)
        return (await self.session.execute(q)).scalar_one_or_none()

    async def get_by_user_id(self, user_id: UUID) -> Patient | None:
        q = select(Patient).where(Patient.user_id == user_id).limit(1)
        return (await self.session.execute(q)).scalar_one_or_none()

    async def search(
        self,
        query: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Patient], int]:
        base = select(Patient)
        if query:
            term = f"%{query.strip()}%"
            base = base.where(
                or_(
                    Patient.last_name.ilike(term),
                    Patient.first_name.ilike(term),
                    Patient.medical_record_number.ilike(term),
                )
            )

        count_q = select(func.count()).select_from(base.subquery())
        total = (await self.session.execute(count_q)).scalar_one()

        q = base.order_by(Patient.last_name, Patient.first_name).offset(offset).limit(limit)
        patients = list((await self.session.execute(q)).scalars().all())
        return patients, total

    async def mrn_exists(self, mrn: str) -> bool:
        q = select(Patient.id).where(Patient.medical_record_number == mrn)
        return (await self.session.execute(q)).scalar_one_or_none() is not None

    async def generate_mrn(self) -> str:
        """Generate next sequential medical record number."""
        q = select(func.count()).select_from(Patient)
        count = (await self.session.execute(q)).scalar_one()
        return f"MRN-{count + 1:06d}"
