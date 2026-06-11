#!/usr/bin/env python
"""
Seed script: Veritabanına ön tanımlı kullanıcıları ekler.
superadmin, manager, frontdesk, housekeeping, accounting, maintenance, fb, hr, guest
Çalıştırmak için: python seed.py
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.user import User
from app.core.auth import get_password_hash

async def seed():
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Önce mevcut kullanıcıları temizle (opsiyonel)
        from sqlalchemy import delete
        await session.execute(delete(User))

        users_data = [
            {"email": "superadmin@hotelops.com", "full_name": "Super Admin", "role": "superadmin", "password": "Super123!"},
            {"email": "manager@hotelops.com", "full_name": "Manager User", "role": "manager", "password": "Manager123!"},
            {"email": "frontdesk@hotelops.com", "full_name": "Front Desk Officer", "role": "frontdesk", "password": "Front123!"},
            {"email": "housekeeping@hotelops.com", "full_name": "Housekeeping Staff", "role": "housekeeping", "password": "House123!"},
            {"email": "accounting@hotelops.com", "full_name": "Accountant", "role": "accounting", "password": "Acc123!"},
            {"email": "maintenance@hotelops.com", "full_name": "Maintenance Staff", "role": "maintenance", "password": "Main123!"},
            {"email": "fb@hotelops.com", "full_name": "F&B Manager", "role": "fb", "password": "FB123!"},
            {"email": "hr@hotelops.com", "full_name": "HR Manager", "role": "hr", "password": "HR123!"},
            {"email": "guest@hotelops.com", "full_name": "Guest User", "role": "guest", "password": "Guest123!"},
        ]

        for data in users_data:
            user = User(
                email=data["email"],
                hashed_password=get_password_hash(data["password"]),
                full_name=data["full_name"],
                role=data["role"],
                is_active=True
            )
            session.add(user)

        await session.commit()
        print("✅ Seed işlemi tamamlandı. 9 kullanıcı eklendi.")
        for data in users_data:
            print(f"   {data['role']}: {data['email']} / {data['password']}")

if __name__ == "__main__":
    asyncio.run(seed())
