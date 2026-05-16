import duckdb

from config.settings import settings


connection = duckdb.connect(
    settings.DUCKDB_PATH
)
