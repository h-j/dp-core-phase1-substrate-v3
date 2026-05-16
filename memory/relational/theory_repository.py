class TheoryRepository:

    def save(self, theory):

        return {
            "status": "stored",
            "theory_id": theory.id
        }
