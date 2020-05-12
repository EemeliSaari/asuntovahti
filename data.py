from dataclasses import dataclass, asdict
from typing import List, Tuple, Dict
from datetime import datetime


@dataclass
class HouseEntry:
    id: int
    url: str
    description: str
    rooms: int
    room_configuration: str
    price: int
    published: datetime
    size: int
    address: str
    district: str
    city: str
    country: str
    year: int
    building_type: str
    longitude: float
    latitude: float
    brand_name: str
    price_changed: datetime
    visits: int
    visits_weekly: int

    def asdict(self):
        """Dataclass as dictionary"""
        data = asdict(self)
        for k, v in data.items():
            if isinstance(v, datetime):
                data[k] = v.strftime('%Y-%m-%dT%H:%M:%SZ')
        return data

    @classmethod
    def fields(cls) -> List[str]:
        """Dataclass field names as string"""
        return list(cls.__dataclass_fields__.keys())
