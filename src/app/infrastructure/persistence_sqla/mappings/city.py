"""
SQLAlchemy mapping for City table metadata.
"""

from sqlalchemy import Integer, String, Float, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import mapped_column

from app.infrastructure.persistence_sqla.registry import mapping_registry


def map_cities_table() -> None:
    """Map City entity to database table."""
    # Idempotency guard: don't remap if already present
    if "cities" in mapping_registry.metadata.tables:
        return
    
    @mapping_registry.mapped
    class CitiesTable:
        __tablename__ = "cities"
        
        # Primary key
        id = mapped_column(Integer, primary_key=True, index=True)
        
        # City information
        city_id = mapped_column(Integer, index=True)
        name = mapped_column(String(100), nullable=False, index=True)
        state_id = mapped_column(String(20), nullable=True, index=True)
        state_code = mapped_column(String(10), nullable=True, index=True)
        state_name = mapped_column(String(100), nullable=True)
        country_id = mapped_column(Integer, nullable=False, index=True)
        country_code = mapped_column(String(2), nullable=True, index=True)
        country_name = mapped_column(String(100), nullable=True)
        latitude = mapped_column(Float, nullable=True)
        longitude = mapped_column(Float, nullable=True)
        wikiDataId = mapped_column(String(50), nullable=True, index=True)
        
        # Add constraints for coordinates
        __table_args__ = (
            CheckConstraint('latitude >= -90 AND latitude <= 90', name='check_city_latitude_range'),
            CheckConstraint('longitude >= -180 AND longitude <= 180', name='check_city_longitude_range'),
            UniqueConstraint('city_id', 'country_id', name='uq_cities_city_country'),
        )
    
    # Keep only table metadata for create_all
