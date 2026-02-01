from app.db.db import engine
from app.db.base import Base
import app.db.models  # importante: registra modelos

print("USANDO:", engine.url)
print("REGISTRADAS:", list(Base.metadata.tables.keys()))

Base.metadata.create_all(bind=engine)
print("Tablas creadas correctamente")