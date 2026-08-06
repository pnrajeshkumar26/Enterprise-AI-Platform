from datetime import datetime


class RuntimeMetrics:
    def __init__(self):
        self.started_at = datetime.utcnow()

        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0

        self.model_loaded_at = None

    def request(self):
        self.total_requests += 1

    def success(self):
        self.successful_requests += 1

    def failure(self):
        self.failed_requests += 1

    def set_model_loaded(self):
        self.model_loaded_at = datetime.utcnow()


runtime_metrics = RuntimeMetrics()