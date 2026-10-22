"""A small pure-Python k-nearest-neighbors supervised-learning policy.

Training is performed by the data-generation script. k-NN 'fits' by retaining
labeled examples and predicts labels by comparing new examples with training data.
No extra packages (NumPy, scikit-learn) are required inside Webots.
"""
import json
from heapq import nsmallest

LABELS = ('forward', 'turn_left', 'turn_right')


class KNNPolicy:
    def __init__(self, examples, k=3):
        self.examples = examples
        self.k = k
        if not examples:
            raise ValueError('Training examples are empty')

    @classmethod
    def from_json(cls, filename):
        with open(filename, encoding='utf-8') as f:
            obj = json.load(f)
        return cls(obj['examples'], obj.get('k', 3))

    def predict(self, x):
        """x = [right_front_proximity, left_front_proximity, signed_goal_bearing].

        Sensors normalized 0..1, bearing normalized -1..1. Returns action id.
        """
        if len(x) != 3:
            raise ValueError('Expected 3 features')
        # Weight the close-obstacle sensors strongly, since collision avoidance
        # must have priority over the heading to the destination.
        nearest = []
        for sample in self.examples:
            a, b, c, label = sample
            d = 9.0 * (a - x[0]) ** 2 + 9.0 * (b - x[1]) ** 2 + 5.0 * (c - x[2]) ** 2
            nearest.append((d, int(label)))
        nearest = nsmallest(self.k, nearest, key=lambda el: el[0])
        scores = [0.0, 0.0, 0.0]
        for dist, label in nearest[:self.k]:
            # Slightly favor closer neighbors.
            scores[label] += 1.0 / (0.02 + dist)
        return max(range(3), key=lambda i: scores[i])
