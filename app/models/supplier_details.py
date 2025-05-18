from sqlalchemy import Column, Integer, String, ForeignKey, DateTime,Date,Text,Index
from app.core.database import Base
from sqlalchemy.orm import relationship
from datetime import date

class UploadLog(Base):
    __tablename__ = "upload_logs"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String)  
    message = Column(String)
    timestamp = Column(DateTime)

    supplier = relationship("User", back_populates="upload_logs")
    __table_args__ = (
        Index("idx_uploadlog_supplier_status", "supplier_id", "status"),
        Index("idx_uploadlog_status", "status"),
    )


class Certification(Base):
    __tablename__ = "certifications"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    issued_by = Column(String(255), nullable=True)
    issued_at = Column(Date, nullable=False, default=date.today)
    expires_at = Column(Date, nullable=True)
    file_url = Column(Text, nullable=True)
    supplier_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    supplier = relationship("User", back_populates="certifications")

    __table_args__ = (
        Index("idx_certification_supplier_issued", "supplier_id", "issued_at"),
    )