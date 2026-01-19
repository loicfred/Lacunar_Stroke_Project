class Notification:
    def __init__(self, **kwargs):
        self.id = kwargs.get("ID")
        self.patient_id = kwargs.get("patient_id")
        self.title = kwargs.get("title")
        self.message = kwargs.get("message")
        self.timestamp = kwargs.get("timestamp")
        self.type = kwargs.get("type")