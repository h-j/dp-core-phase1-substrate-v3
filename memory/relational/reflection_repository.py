class ReflectionRepository:

    def save(self, reflection):

        return {
            "status": "stored",
            "reflection_id": reflection.id
        }
