from app.database import SessionLocal
from app import models
from app.analyzer import analyze_text


def backfill() -> None:
    db = SessionLocal()
    try:
        contracts = db.query(models.Contract).all()
        updated = 0
        for contract in contracts:
            db.query(models.ClauseFlag).filter(models.ClauseFlag.contract_id == contract.id).delete(synchronize_session=False)
            new_flags = analyze_text(contract.text)
            for f in new_flags:
                db.add(models.ClauseFlag(contract_id=contract.id, **f))
            updated += 1
        db.commit()
        print(f"Re-analyzed {updated} contracts. New flags have been saved.")
    finally:
        db.close()


if __name__ == "__main__":
    backfill()


