Error
The error InFailedSqlTransaction: current transaction is aborted, commands ignored until end of transaction block occurred because:
A previous operation failed (e.g., constraint violation due to duplicate email)
The transaction remained in an "aborted" state
There was no rollback to clear the session state
Subsequent operations failed because the session remained corrupted



siempre usar uv nada pip 


USER = "postgres"
PASSWORD = "changethis"
DB = "anvil_db"
HOST = "localhost"
PORT = 5432
DRIVER = "psycopg"