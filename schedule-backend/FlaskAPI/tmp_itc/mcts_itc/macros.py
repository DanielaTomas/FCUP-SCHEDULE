DAYS = 5
PERIODS_PER_DAY = 9
HARD_PENALTY = 10
HARD_WEIGHT = 10
ALL_SLOTS = set((weekday, timeslot) for weekday in range(DAYS) for timeslot in range(PERIODS_PER_DAY))