"""
SQLAlchemy mapping for Country table metadata.
"""

from sqlalchemy import Integer, String, Float, JSON, CheckConstraint
from sqlalchemy.orm import mapped_column

from app.infrastructure.persistence_sqla.registry import mapping_registry


def map_countries_table() -> None:
    """Map Country entity to database table."""
    # Idempotency guard: don't remap if already present
    if "countries" in mapping_registry.metadata.tables:
        return
    
    @mapping_registry.mapped
    class CountriesTable:
        __tablename__ = "countries"
        
        # Primary key
        id = mapped_column(Integer, primary_key=True, index=True)
        
        # Country information
        country_id = mapped_column(Integer, index=True)
        name = mapped_column(String(100), nullable=False, index=True)
        iso3 = mapped_column(String(3), unique=True, nullable=False, index=True)
        iso2 = mapped_column(String(2), nullable=True, index=True)
        numeric_code = mapped_column(String(3), nullable=True)
        phonecode = mapped_column(String(20), nullable=True)
        capital = mapped_column(String(100), nullable=True)
        currency = mapped_column(String(3), nullable=True)
        currency_name = mapped_column(String(50), nullable=True)
        currency_symbol = mapped_column(String(10), nullable=True)
        tld = mapped_column(String(10), nullable=True)
        native = mapped_column(String(100), nullable=True)
        nationality = mapped_column(String(100), nullable=True)
        timezones = mapped_column(JSON, nullable=True)  # Store as JSON array
        latitude = mapped_column(Float, nullable=True)
        longitude = mapped_column(Float, nullable=True)
        emoji = mapped_column(String(10), nullable=True)
        emojiU = mapped_column(String(20), nullable=True)
        region = mapped_column(String(50), nullable=True, index=True)
        subregion = mapped_column(String(50), nullable=True, index=True)
        
        # Add constraints for coordinates
        __table_args__ = (
            CheckConstraint('latitude >= -90 AND latitude <= 90', name='check_latitude_range'),
            CheckConstraint('longitude >= -180 AND longitude <= 180', name='check_longitude_range'),
        )
    
    # Keep only table metadata for create_all
