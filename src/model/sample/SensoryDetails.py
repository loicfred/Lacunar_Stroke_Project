from datetime import datetime

class SensoryDetails:
    def __init__(self, left_sensory_score, right_sensory_score, affected_side, asymmetry_label, impact_tier=0):
        self.left_sensory_score = left_sensory_score
        self.right_sensory_score = right_sensory_score
        self.affected_side = affected_side
        self.asymmetry_label = asymmetry_label
        self.impact_tier = impact_tier

        self.timestamp = datetime.now()

        self.asymmetry_index = self.calculate_asymmetry_index()
        self.response_strength = None


    def calculate_asymmetry_diff(self):
        return abs(self.left_sensory_score - self.right_sensory_score)

    def calculate_avg_asymmetry(self):
        return (self.left_sensory_score + self.right_sensory_score) / 2

    def calculate_asymmetry_index(self):
        avg = self.calculate_avg_asymmetry()
        asym_diff = self.calculate_asymmetry_diff()
        self.asymmetry_index = asym_diff / avg if avg > 0 else 0.0
        return self.asymmetry_index

