class SensoryDetails:
    def __init__(self, left_sensory_score, right_sensory_score, affected_side, asymmetry_label):
        self.left_sensory_score = left_sensory_score
        self.right_sensory_score = right_sensory_score
        self.affected_side = affected_side
        self.asymmetry_label = asymmetry_label

        self.avg_asymmetry = self.calculate_avg_asymmetry()
        self.asymmetry_difference = self.calculate_asymmetry_diff()
        self.asymmetry_index = self.calculate_asymmetry_index()
        self.severity = None


    def calculate_asymmetry_diff(self):
        self.asymmetry_difference = abs(self.left_sensory_score - self.right_sensory_score)
        return self.asymmetry_difference

    def calculate_avg_asymmetry(self):
        self.avg_asymmetry = (self.left_sensory_score + self.right_sensory_score) / 2
        return self.avg_asymmetry

    def calculate_asymmetry_index(self):
        avg = self.calculate_avg_asymmetry()
        asym_diff = self.calculate_asymmetry_diff()
        self.asymmetry_index = asym_diff / avg if avg > 0 else 0.0
        return self.asymmetry_index
