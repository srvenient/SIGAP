from src.server.audit.application.audit_recorder import AuditRecorder
from src.server.audit.domain.audit_log import Actor, AuditAction
from src.server.parking.domain.parking_lot import Occupancy, ParkingLot, ParkingLotUpdate
from src.server.parking.domain.parking_lot_repository import ParkingLotRepository
from src.server.transaction.domain.transaction_repository import TransactionRepository


class ParkingService:
    def __init__(
            self,
            repository: ParkingLotRepository,
            transactions: TransactionRepository,
            audit: AuditRecorder,
    ):
        self.repository = repository
        self.transactions = transactions
        self.audit = audit

    async def get(self) -> ParkingLot:
        return await self.repository.get_default()

    async def occupancy(self) -> Occupancy:
        lot = await self.repository.get_default()
        return Occupancy.of(lot.capacity, await self.transactions.count_inside(lot.id))

    async def update(self, data: ParkingLotUpdate, actor: Actor) -> ParkingLot:
        lot = await self.repository.get_default()
        changes = {
            field: {"anterior": getattr(lot, field), "nuevo": value}
            for field, value in data.model_dump(exclude_unset=True, exclude_none=True).items()
            if getattr(lot, field) != value
        }
        if not changes:
            return lot

        for field, change in changes.items():
            setattr(lot, field, change["nuevo"])
        self.audit.record(
            AuditAction.PARKING_UPDATED, actor, "parking_lot", lot.id, lot.name, detail=changes
        )
        return await self.repository.save(lot)
