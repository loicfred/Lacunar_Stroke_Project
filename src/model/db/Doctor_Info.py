class Doctor_Info:
    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.first_name = kwargs.get("first_name")
        self.last_name = kwargs.get("last_name")
        self.title = kwargs.get("title")
        self.qualification = kwargs.get("qualification")
        self.profession = kwargs.get("profession")