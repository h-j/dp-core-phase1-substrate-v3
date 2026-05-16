class OntologyGraphStore:

    def register_concept(self, concept: str):

        return {
            "concept": concept,
            "status": "registered"
        }
