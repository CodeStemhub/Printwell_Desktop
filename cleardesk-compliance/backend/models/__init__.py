from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Float, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class User(Base):
    """User account model."""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String)
    organization = Column(String)
    industry = Column(String, default="accounting")
    subscription_tier = Column(String, default="free")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")


class Document(Base):
    """Business document model."""
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=True)
    
    # File info
    filename = Column(String, nullable=False)
    storage_url = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    input_method = Column(String, nullable=False)  # upload, scan, email
    
    # Processing status
    status = Column(String, default="pending")  # pending, processing, ready, flagged, complete
    
    # OCR results
    extracted_text = Column(Text)
    ocr_method = Column(String)  # tesseract, google_vision, pdfplumber
    ocr_confidence = Column(Float)
    
    # Classification
    classified_type = Column(String)  # GRA_VAT_RETURN, SSNIT_CONTRIBUTION, etc.
    classification_confidence = Column(Float)
    issuing_organization = Column(String)
    document_period = Column(String)
    key_identifiers = Column(JSONB)
    
    # Extraction
    extracted_data = Column(JSONB)
    
    # Validation
    flags = Column(JSONB, default=list)
    validation_status = Column(String, default="not_validated")  # valid, has_flags, needs_review
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="documents")
    chat_session = relationship("ChatSession", back_populates="documents")


class ChatSession(Base):
    """Agent chat session model."""
    __tablename__ = "chat_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    module = Column(String, default="compliance")  # compliance, realestate (future)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    documents = relationship("Document", back_populates="chat_session")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at")


class ChatMessage(Base):
    """Individual chat message model."""
    __tablename__ = "chat_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String, nullable=False)  # user, agent, system
    content = Column(Text, nullable=False)
    message_metadata = Column(JSONB, default=dict)  # For storing references to documents, actions, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")


class Flag(Base):
    """Validation flag for document issues."""
    __tablename__ = "flags"
    
    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    flag_type = Column(String, nullable=False)  # missing_field, calculation_error, low_confidence, format_issue
    field_name = Column(String)
    message = Column(String, nullable=False)
    severity = Column(String, default="medium")  # low, medium, high, critical
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
