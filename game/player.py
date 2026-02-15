
class Player:
    def __init__(self, address, start_room):
        self.address = address
        self.current_room = start_room
        self.name = None
        self.level = 1
        self.xp = 0
        self.xp_max = 100
        self.inventory = ['Cyberdeck', 'Neon Blade', 'Stimpack']
        # Simple currency balance
        self.credits = 100
        # Equipment slots
        self.equipment = {
            'head': None,
            'body': None,
            'legs': None,
            'feet': None,
            'hands': None,
            'weapon': None,
            'offhand': None,
            'accessory': None
        }
        self.race = None
        self.char_class = None
        # Default stats
        self.hp = 100
        self.energy = 100
        self.endurance = 100
        self.willpower = 100
        self.strength = 10
        self.tech = 10
        self.speed = 10
        self.abilities = []
        self.apply_race_class()

    def get_attack(self):
        base = getattr(self, 'strength', 10)
        bonus = 0
        eq = getattr(self, 'equipment', {}) or {}
        if eq.get('weapon') == 'Neon Blade':
            bonus += 3
        # Temporary boosts
        if getattr(self, 'attack_boost', 0):
            bonus += int(base * self.attack_boost)
        return base + bonus

    def apply_race_class(self):
        # Set stats/abilities based on race/class
        from game.races_classes import CLASSES, RACES
        if self.race in RACES:
            race = RACES[self.race]
            for stat, value in race["stats"].items():
                setattr(self, stat, value)
            self.abilities.extend(race.get("abilities", []))
        if self.char_class in CLASSES:
            char_class = CLASSES[self.char_class]
            for stat, value in char_class["stats"].items():
                if hasattr(self, stat):
                    setattr(self, stat, getattr(self, stat) + value)
                else:
                    setattr(self, stat, value)
            self.abilities.extend(char_class.get("abilities", []))