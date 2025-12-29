

import time


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
        # Quest log keyed by mission id: {status: 'accepted'|'completed', giver: <npc>, title: <title>}
        self.quests = {}
        self.apply_race_class()

    def _queue_notice(self, text):
        if not text:
            return
        notices = getattr(self, '_pending_notices', None)
        if not isinstance(notices, list):
            notices = []
        notices.append(str(text))
        # Keep it bounded.
        self._pending_notices = notices[-20:]


    def pop_notices(self):
        notices = getattr(self, '_pending_notices', None)
        if not isinstance(notices, list) or not notices:
            return []
        self._pending_notices = []
        return notices


    def refresh_timed_effects(self, now=None):
        if now is None:
            now = time.time()

        expires_at = getattr(self, 'attack_boost_expires_at', None)
        if expires_at is not None:
            expired_source = getattr(self, 'attack_boost_source', None)
            try:
                exp = float(expires_at)
            except Exception:
                exp = None

            if exp is not None and now >= exp:
                try:
                    delattr(self, 'attack_boost_expires_at')
                except Exception:
                    self.attack_boost_expires_at = None

                # If Red Eye was used, keep its permanent +10%; otherwise clear boost.
                if getattr(self, 'red_eye_used', False):
                    self.attack_boost = 0.10
                    self.attack_boost_source = 'red_eye'
                else:
                    self.attack_boost = 0
                    try:
                        delattr(self, 'attack_boost_source')
                    except Exception:
                        self.attack_boost_source = None

                if expired_source == 'adrenaline':
                    self._queue_notice("Your adrenaline rush fades.")
                elif expired_source == 'red_eye':
                    # Red Eye should not be expiring; keep message generic if this happens.
                    self._queue_notice("The edge fades.")
                else:
                    self._queue_notice("The boost fades.")


    def get_attack(self):
        self.refresh_timed_effects()

        base = getattr(self, 'strength', 10)
        bonus = 0
        eq = getattr(self, 'equipment', {}) or {}
        if eq.get('weapon') == 'Neon Blade':
            bonus += 3
        # Temporary boosts
        if getattr(self, 'attack_boost', 0):
            bonus += int(base * getattr(self, 'attack_boost'))
        return base + bonus

    def apply_race_class(self):
        # Set stats/abilities based on race/class
        from game.races_classes import RACES, CLASSES
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