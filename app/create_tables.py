from app.database import datasync_engine
from app.models import Base


Base.metadata.create_all(bind=datasync_engine)

print("DataSync tables created.")