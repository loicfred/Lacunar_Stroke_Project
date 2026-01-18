class User:
    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.email = kwargs.get("email")
        self.role = kwargs.get("role")