"""Clear only the note and verification_status tables. Frontend will reflect after refresh."""
from app import create_app, db
from app.models import Note, VerificationStatus

def clear_notes():
    app = create_app()
    with app.app_context():
        try:
            num_verifications = VerificationStatus.query.delete()
            print(f"Deleted {num_verifications} VerificationStatus rows.")
            num_notes = Note.query.delete()
            print(f"Deleted {num_notes} Note rows.")
            db.session.commit()
            print("Note table cleared. Refresh the notes page in your browser.")
        except Exception as e:
            db.session.rollback()
            print(f"Failed: {e}")
            raise

if __name__ == "__main__":
    clear_notes()
