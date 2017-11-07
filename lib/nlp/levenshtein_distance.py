c_levenshtein = False

try:
    import numpy as np
    from weighted_levenshtein import lev
    c_levenshtein = True
except ImportError:
    np, lev = None, None
    pass

deletion_costs, insertion_costs, substitution_costs = None, None, None


class Levenshtein(object):
    """
    Calculates the Levenshtein distance between two words

    For Example:
        levenshtein = Levenshtein(word1='hello',word2='helllo', max_threshold=3)
        output = levenshtein.levenshtein_distance()
        print output
        >> 1

        levenshtein = Levenshtein(word1='beautiful',word2='beauty', max_threshold=3)
        output = levenshtein.levenshtein_distance()
        print output
        >> 3

    Attributes:
        word1: String that needs to compare to
        word2: String that need to compare with
        max_threshold: max distance between the two words can have

    NOTE: Since, minimum edit distance is time consuming process, we have defined max_threshold attribute.
    So, whenever distance exceeds the max_threshold the function will break and return the max_threshold else
    it will return levenshtein distance
    """

    def __init__(self, word1, word2, max_threshold=3):
        """Initializes a Levenshtein object

        Args:
            word1: String that needs to compare to
            word2: String that need to compare with
            max_threshold: max distance between the two words can have
        """

        self.word1 = word1
        self.word2 = word2
        self.max_threshold = max_threshold

    def edit_distance(self):
        global deletion_costs, insertion_costs, substitution_costs
        if c_levenshtein:
            if None in [deletion_costs, insertion_costs, substitution_costs]:
                deletion_costs = np.ones(256, dtype=np.float64)
                insertion_costs = np.ones(256, dtype=np.float64)
                substitution_costs = np.array([256, 256], dtype=np.float64)
                substitution_costs.fill(2)
            return min(self.max_threshold, lev(self.word1, self.word2, insert_costs=insertion_costs,
                                               delete_costs=deletion_costs, substitute_costs=substitution_costs))
        else:
            return self.levenshtein_distance()

    def levenshtein_distance(self):
        """Returns the levenshtein distance between two words

        Returns:
            Returns the levenshtein distance between two words
            For example:
                levenshtein = Levenshtein(word1='hello',word2='helllo', max_threshold=3)
                output = levenshtein.levenshtein_distance()
                print output
                >> 1

                levenshtein = Levenshtein(word1='beautiful',word2='beauty', max_threshold=3)
                output = levenshtein.levenshtein_distance()
                print output
                >> 3

        """
        cost_sub = 2
        cost_ins = 1
        cost_del = 1
        if len(self.word1) > len(self.word2):
            self.word1, self.word2 = self.word2, self.word1
        distances = range(len(self.word1) + 1)
        for index2, char2 in enumerate(self.word2):
            newDistances = [index2 + 1]
            for index1, char1 in enumerate(self.word1):
                if char1 == char2:
                    newDistances.append(distances[index1])
                else:
                    newDistances.append(min((distances[index1] + cost_sub,
                                             distances[index1 + 1] + cost_ins,
                                             newDistances[-1] + cost_del)))
            distances = newDistances
            if min(newDistances) > self.max_threshold:
                return self.max_threshold

        return distances[-1]
