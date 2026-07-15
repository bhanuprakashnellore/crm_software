"""Seed the database with a few sample HCPs so the demo has data to search/log against.
Run with: python seed.py
"""
from app.database import Base, engine, SessionLocal
from app.models import HCP

Base.metadata.create_all(bind=engine)

SAMPLE_HCPS = [
    dict(name="Dr. Anika Rao", specialty="Cardiology", institution="Apollo Hospitals",
         npi_number="1234567890", email="anika.rao@example.com", city="Hyderabad", engagement_tier="KOL"),
    dict(name="Dr. Vikram Sinha", specialty="Endocrinology", institution="Fortis Healthcare",
         npi_number="1234567891", email="vikram.sinha@example.com", city="Delhi", engagement_tier="High"),
    dict(name="Dr. Meera Iyer", specialty="Oncology", institution="Tata Memorial Hospital",
         npi_number="1234567892", email="meera.iyer@example.com", city="Mumbai", engagement_tier="KOL"),
    dict(name="Dr. Sanjay Kapoor", specialty="General Medicine", institution="Manipal Hospitals",
         npi_number="1234567893", email="sanjay.kapoor@example.com", city="Bengaluru", engagement_tier="Medium"),
]

if __name__ == "__main__":
    db = SessionLocal()
    try:
        for record in SAMPLE_HCPS:
            exists = db.query(HCP).filter(HCP.name == record["name"]).first()
            if not exists:
                db.add(HCP(**record))
        db.commit()
        print(f"Seeded {len(SAMPLE_HCPS)} sample HCPs (skipping any that already exist).")
    finally:
        db.close()
