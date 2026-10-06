"""
One-off script to create the first admin account (there is no admin
self-registration by design).

Usage:
    python -m scripts.create_admin --email admin@college.edu --name "Admin" --password "ChangeMe123"
"""
import argparse

from app.core.security import hash_password
from app.database import SessionLocal
from app.models import User, UserRole


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--password", required=True)
    args = parser.parse_args()

    with SessionLocal() as db:
        existing = db.query(User).filter(User.email == args.email.lower()).first()
        if existing:
            print(f"A user with email {args.email} already exists (role={existing.role.value}).")
            return
        admin = User(
            full_name=args.name,
            email=args.email.lower(),
            password_hash=hash_password(args.password),
            role=UserRole.admin,
            must_change_password=False,
        )
        db.add(admin)
        db.commit()
        print(f"Created admin {args.email}.")


if __name__ == "__main__":
    main()
