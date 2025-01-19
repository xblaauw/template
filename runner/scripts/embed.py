from lib.database import get_db, get_df, Base


Embeddings = Base.classes.embeddings

with get_db() as session:
    results = session.query(Embeddings).order_by(Embeddings.timestamp.desc()).all()