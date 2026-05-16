class PersistenceMetrics:

    def record(self, metric_name: str):

        return {
            "metric": metric_name,
            "status": "recorded"
        }
