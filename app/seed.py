import asyncio
from sqlalchemy import select
from app.core.security import get_password_hash
from app.db.session import AsyncSessionLocal
from app.models.auth_model import User, UserRole

DEFAULT_USERS = [
    {
        "email": "admin@swayambhuinfo.com",
        "full_name": "Executive Admin",
        "password": "Admin@2026",
        "role": UserRole.ADMIN,
    },
    {
        "email": "manager@swayambhuinfo.com",
        "full_name": "Plant Manager",
        "password": "Manager@2026",
        "role": UserRole.MANAGER,
    },
    {
        "email": "operator@swayambhuinfo.com",
        "full_name": "Operations & Weighbridge Operator",
        "password": "Operator@2026",
        "role": UserRole.OPERATOR,
    },
]


async def seed_users():
    async with AsyncSessionLocal() as session:
        for udata in DEFAULT_USERS:
            stmt = select(User).where(User.email == udata["email"])
            res = await session.execute(stmt)
            existing = res.scalar_one_or_none()

            if not existing:
                user = User(
                    email=udata["email"],
                    full_name=udata["full_name"],
                    hashed_password=get_password_hash(udata["password"]),
                    role=udata["role"],
                    is_active=True,
                )
                session.add(user)
                print(f"[+] Seeded user: {udata['email']} as {udata['role'].value}")
            else:
                existing.hashed_password = get_password_hash(udata["password"])
                existing.role = udata["role"]
                print(f"[*] Updated existing user: {udata['email']}")

        await session.commit()
        print("[*] Authentication database seeding complete.")


if __name__ == "__main__":
    asyncio.run(seed_users())