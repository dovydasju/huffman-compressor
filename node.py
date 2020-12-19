class HuffmanNode:
    def __init__(self, value, occur=0, left=None, right=None):
        self.value = value
        self.occur = occur
        self.left = left
        self.right = right

    def __lt__(self, other):
        return self.occur < other.occur
