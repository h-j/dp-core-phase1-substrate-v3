from memory.relational.postgres_client import engine


class RelationalStore:

    def healthcheck(self) -> bool:

        return engine is not None
