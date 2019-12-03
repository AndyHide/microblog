class Day:
    def __init__(self, name):
        self.name = name
        self.breakfast = ''
        self.lunch = ''
        self.dinner = ''


class Mealplan:
    def __init__(self):
        self.days = [Day('Monday'), Day('Tuesday'), Day('Wednesday'), Day('Thursday'), Day('Friday')]