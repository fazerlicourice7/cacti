"""
area.py
Python translation of area.{h, cc} from CACTI 7.0
"""

# If needed, import from other modules
# from .cacti_interface import ...
# from .basic_circuit import ...

class Area:
    """
    Python version of the C++ Area class.
    Has fields w, h, plus a stored area if needed.
    """
    def __init__(self):
        self.w = 0.0
        self.h = 0.0
        self._area = 0.0  # We'll store the 'private' area here

    def get_w(self):
        return self.w

    def get_h(self):
        return self.h

    def set_w(self, w_):
        self.w = w_

    def set_h(self, h_):
        self.h = h_

    def set_area(self, a_):
        self._area = a_

    def get_area(self):
        """
        If w and h are nonzero, return w*h; else use the stored area.
        """
        if self.w == 0 and self.h == 0:
            return self._area
        else:
            return self.w * self.h
