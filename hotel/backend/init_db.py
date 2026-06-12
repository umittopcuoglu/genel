#!/usr/bin/env python
"""
Veritabanı tablolarını oluşturur (tüm modeller için Base.metadata.create_all).
Lokal geliştirme için en hızlı yol — Alembic migration'larına gerek yok.

Çalıştırmak için:
    python init_db.py

Varsayılan DB: sqlite+aiosqlite:///./dev.db (.env ile değiştirilebilir).
Tabloları oluşturduktan sonra örnek kullanıcılar için: python seed.py
"""
import asyncio

from app.core.db import engine, Base
import app.models  # tüm modelleri Base.metadata'ya kaydeder (noqa: F401)


async def main() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print("✅ Veritabanı tabloları oluşturuldu.")


if __name__ == "__main__":
    asyncio.run(main())
