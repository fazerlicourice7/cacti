class Area:
    def __init__(self):
        self.w = 0
        self.h = 0
        self.area = 0

    def get_w(self):
        return self.w

    def get_h(self):
        return self.h

    def get_area(self):
        if self.w == 0 and self.h == 0:
            return self.area
        else:
            return self.w * self.h

    def set_w(self, w_):
        self.w = w_

    def set_h(self, h_):
        self.h = h_

    def set_area(self, a_):
        self.area = a_

# Assuming other required imports and classes are defined elsewhere
