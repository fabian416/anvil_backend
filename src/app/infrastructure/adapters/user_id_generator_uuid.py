from app.domain.ports.user_id_generator import UserIdGenerator


class UuidUserIdGenerator(UserIdGenerator):
    def __call__(self) -> int:
        # SQL auto-increment handled by DB; return placeholder int (ignored by ORM)
        # Domain UserId is int now to match DB PK; actual value set on flush
        return 0
