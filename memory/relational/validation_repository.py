class ValidationRepository:

    def save(self, validation):

        return {
            "status": "stored",
            "validation_id": validation.id
        }
