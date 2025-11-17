from app.domain.exceptions.base import DomainError


class CountryNotFoundError(DomainError):
    def __init__(self, country_id: int):
        super().__init__(f"Country with ID {country_id} not found")


class CityNotFoundInCountryError(DomainError):
    def __init__(self, city_id: int, country_id: int):
        super().__init__(
            f"City with ID {city_id} not found in country with ID {country_id}"
        )


