from sqlmodel.ext.asyncio.session import AsyncSession

from src.server.parking.domain.parking_lot import DEFAULT_PARKING_LOT_ID, ParkingLot, ParkingLotNotFound
from src.server.parking.domain.parking_lot_repository import ParkingLotRepository


class PostgresParkingLotRepository(ParkingLotRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_default(self) -> ParkingLot:
        lot = await self.session.get(ParkingLot, DEFAULT_PARKING_LOT_ID)
        if lot is None:
            raise ParkingLotNotFound
        return lot

    async def get_default_for_update(self) -> ParkingLot:
        lot = await self.session.get(
            ParkingLot, DEFAULT_PARKING_LOT_ID, with_for_update=True, populate_existing=True
        )
        if lot is None:
            raise ParkingLotNotFound
        return lot

    async def save(self, lot: ParkingLot) -> ParkingLot:
        self.session.add(lot)
        await self.session.commit()
        await self.session.refresh(lot)
        return lot
