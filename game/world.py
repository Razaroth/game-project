class World:
    def __init__(self):
        self.rooms = {
            # Existing starter area
            'start': {
                'description': 'You are in a small room. The room smells damp and murky, no one has been here in a long time. A small sliver of light peeks through the blinds of a small window.',
                'exits': {'north': 'hall', 'east': 'closet'}
            },
            'hall': {
                'description': 'A long, dark, dingy hallway littered with discarded aug parts. Unfriendly eyes watch from the shadows. Exits are south and north.',
                'exits': {'south': 'start', 'north': 'neon_plaza_approach'}
            },
            'closet': {
                'description': 'A dusty closet, nothing of too much interest. Exits are west.',
                'exits': {'west': 'start'}
            },

            # Cyberdelia — city hub and streets
            'neon_plaza_approach': {
                'description': 'A flickering corridor opens onto the city. Neon bleeds through cracked panels and rain hisses on hot concrete.',
                'exits': {'south': 'hall', 'north': 'neon_plaza'}
            },
            'neon_plaza': {
                'description': 'Neon Plaza: hologram billboards paint the night sky in synth-light. Street vendors hawk chrome implants beside towering vid-screens.',
                'exits': {
                    'south': 'neon_plaza_approach',
                    'east': 'chrome_avenue_w',
                    'west': 'synth_street_w',
                    'north': 'arcology_lobby',
                    'down': 'underground_metro'
                }
            },
            'chrome_avenue_w': {
                'description': 'Chrome Avenue (West): rain-slick metal walkways reflect a thousand neon glyphs. Drones hum overhead.',
                'exits': {'west': 'neon_plaza', 'east': 'chrome_avenue_e', 'south': 'rust_and_circuit'}
            },
            'chrome_avenue_e': {
                'description': 'Chrome Avenue (East): a canyon of glass and steel, AR ads ripple along the facades.',
                'exits': {'west': 'chrome_avenue_w', 'east': 'corporate_lobby'}
            },
            # Note: provide reciprocal path for avenue
            # Use conventional east/west mapping
            'corporate_lobby': {
                'description': 'Corporate Lobby: marble floor, biometric turnstiles, and a waterfall of cascading holo-text.',
                'exits': {'west': 'chrome_avenue_e', 'up': 'server_farm'}
            },
            'server_farm': {
                'description': 'Server Farm: a cathedral of racks, coolant mist drifting between humming stacks. Security ICE crackles in the air.',
                'exits': {'down': 'corporate_lobby'}
            },
            'rust_and_circuit': {
                'description': 'Rust & Circuit (Bar): oil-stained booths, synthwave pulsing, and the scent of ozone and whiskey.',
                'exits': {'north': 'chrome_avenue_w'}
            },

            'synth_street_w': {
                'description': 'Synth Street (West): patchwork concrete, tangled cabling, and street docs plying their trade.',
                'exits': {'east': 'synth_street_e', 'south': 'back_alley_w', 'north': 'data_leak'}
            },
            'synth_street_e': {
                'description': 'Synth Street (East): basslines thump from distant clubs; rain turns the light into liquid color.',
                'exits': {'west': 'synth_street_w', 'north': 'pulse_reactor'}
            },
            'data_leak': {
                'description': 'The Data Leak (Bar): hackers whisper over phosphor-green cocktails; cracked terminals glow along the bar.',
                'exits': {'south': 'synth_street_w'}
            },
            'pulse_reactor': {
                'description': 'Pulse Reactor (Club): subsonic beats shake the ribcage as light fractals explode across the dance floor.',
                'exits': {'south': 'synth_street_e'}
            },

            # Back alleys and markets
            'back_alley_w': {
                'description': 'Back Alley (West): steam vents hiss, graffiti flickers with reactive inks. It feels watched.',
                'exits': {'north': 'synth_street_w', 'east': 'back_alley_e', 'south': 'night_market'}
            },
            'back_alley_e': {
                'description': 'Back Alley (East): dumpsters overflow with cybernetic scrap; the hum of jury-rigged power lines fills the air.',
                'exits': {'west': 'back_alley_w', 'east': 'neon_alley_s'}
            },
            'night_market': {
                'description': 'Night Market: tarps and stalls under neon rain—contraband biosoft, knockoff optics, and rare firmware.',
                'exits': {'north': 'back_alley_w', 'east': 'black_market_bazaar'}
            },
            'black_market_bazaar': {
                'description': 'Black Market Bazaar: encrypted auctions buzz on handhelds; mercs barter in hushed tones.',
                'exits': {'west': 'night_market'}
            },

            # Neon Alley and clubs
            'neon_alley_n': {
                'description': 'Neon Alley (North): cramped walls glow with animated kanji; puddles ripple with color.',
                'exits': {'south': 'neon_alley_s', 'east': 'club_nexus'}
            },
            'neon_alley_s': {
                'description': 'Neon Alley (South): cables loop like ivy; a backdoor thumps with bass.',
                'exits': {'north': 'neon_alley_n', 'west': 'back_alley_e', 'east': 'holo_dive'}
            },
            'club_nexus': {
                'description': 'Club Nexus: chromed monolith speakers, laser fog, VIP mezzanines prowled by corpos and fixers.',
                'exits': {'west': 'neon_alley_n'}
            },
            'holo_dive': {
                'description': 'The Holo-Dive: retro CRT cages and full-sensory booths; patrons drift through curated illusions.',
                'exits': {'west': 'neon_alley_s'}
            },

            # Arcology stack
            'arcology_lobby': {
                'description': 'Arcology Tower Lobby: mirrored chrome, whisper-quiet lifts, and a concierge drone that never blinks.',
                'exits': {'south': 'neon_plaza', 'up': 'arcology_residential'}
            },
            'arcology_residential': {
                'description': 'Arcology Residential: endless corridors of identical doors, soft white noise masking the city’s roar.',
                'exits': {'down': 'arcology_lobby', 'up': 'arcology_penthouse'}
            },
            'arcology_penthouse': {
                'description': 'Arcology Penthouse: panoramic cityscape under stormclouds; a minimalist throne of glass and neon.',
                'exits': {'down': 'arcology_residential'}
            },

            # Underground
            'underground_metro': {
                'description': 'Underground Metro: hollow tunnels, vending machines selling stamina chems, and a distant train’s wail.',
                'exits': {'up': 'neon_plaza', 'south': 'scrapyard'}
            },
            'scrapyard': {
                'description': 'Scrapyard: mountains of rusted bots and drone wings; scavengers pick through sparks and rain.',
                'exits': {'north': 'underground_metro'}
            }
        }
        self.start_room = 'start'
        # Stationary NPCs per room (name, role)
        self.npcs_by_room = {
            'hall': [
                {'name': 'Rook', 'role': 'Fixer'}
            ],
            'neon_plaza': [
                {'name': 'Kite', 'role': 'Courier'}
            ],
            'synth_street_w': [
                {'name': 'Doc Kira', 'role': 'Street Doc'}
            ],
            'rust_and_circuit': [
                {'name': 'Grease', 'role': 'Bartender'},
                {'name': 'Mox', 'role': 'Bouncer'}
            ],
            'data_leak': [
                {'name': 'Patch', 'role': 'Bartender'},
                {'name': 'Glimmer', 'role': 'Dealer'}
            ],
            'night_market': [
                {'name': 'Hex', 'role': 'Vendor'},
                {'name': 'Silk', 'role': 'Vendor'}
            ],
            'black_market_bazaar': [
                {'name': 'Cipher', 'role': 'Fence'}
            ],
            'club_nexus': [
                {'name': 'DJ Void', 'role': 'DJ'},
                {'name': 'Nyx', 'role': 'Bartender'}
            ],
            'holo_dive': [
                {'name': 'Vera', 'role': 'Attendant'}
            ],
            'corporate_lobby': [
                {'name': 'Concierge-7', 'role': 'Receptionist'}
            ],
            'arcology_lobby': [
                {'name': 'Porter Drone', 'role': 'Concierge'}
            ]
        }

        # Basic missions offered by NPCs (kept simple: fetch/turn-in item quests)
        # Each mission is identified by a stable id so it can be persisted per account.
        self.missions_by_npc = {
            # Early-game mission in starter area
            'rook': {
                'id': 'rook_chip_run',
                'title': 'Chip Run',
                'description': "Bring me an Encrypted Chip. I'll pay and bump your rep.",
                'required_item': 'Encrypted Chip',
                'reward_xp': 25,
                'reward_credits': 40,
                'dialog': {
                    'offer': "Rook leans against a cracked panel, eyes flicking to every shadow. 'You look capable. I need a chip moved off-grid.'",
                    'accepted': "Rook smirks. 'Good. Quiet hands, quiet feet. Come back with the chip and nobody has to know you were here.'",
                    'reminder': "Rook taps two fingers against his temple. 'Encrypted Chip. Don't bring me drama, bring me data.'",
                    'ready': "Rook's gaze locks on your pocket. 'That's it. Slide it over.'",
                    'success': "Rook pockets the chip without looking. 'Clean work. The city's got room for people like you.'",
                    'completed': "Rook gives a short nod. 'We already did business. Keep moving.'",
                },
            },
            # Hub mission that nudges players toward the corporate branch
            'kite': {
                'id': 'kite_corporate_access',
                'title': 'Corporate Access',
                'description': "I need a Visitor Pass. Get one from the corporate lobby and bring it back fast.",
                'required_item': 'Visitor Pass',
                'reward_xp': 25,
                'reward_credits': 50,
                'dialog': {
                    'offer': "Kite adjusts a rain-slick hood and checks a wrist display. 'Corpos changed the locks again. I need a pass before the window closes.'",
                    'accepted': "Kite exhales, relief hidden behind swagger. 'Nice. In and out. Don't let the scanners taste fear.'",
                    'reminder': "Kite glances up at the tower lights. 'Visitor Pass. Corporate Lobby. Move like you belong.'",
                    'ready': "Kite's hand is already out. 'Pass first. Questions later.'",
                    'success': "Kite flips the pass between two fingers, then vanishes it into a sleeve. 'You're faster than you look. Here's your cut.'",
                    'completed': "Kite grins. 'That job's done. Listen - if something pings your name, it wasn't me.'",
                },
            },
            # Bar/market missions using items that already exist in loot/shop tables
            'grease': {
                'id': 'grease_spare_parts',
                'title': 'Spare Parts',
                'description': "Find a Cyberdeck Fragment. I'll trade credits for it.",
                'required_item': 'Cyberdeck Fragment',
                'reward_xp': 20,
                'reward_credits': 35,
                'dialog': {
                    'offer': "Grease wipes a glass with a rag that has seen better decades. 'Got a broken deck on my bench. Need a fragment to make it sing again.'",
                    'accepted': "Grease nods toward the door. 'Bring it back dry. Rain ruins everything out there.'",
                    'reminder': "Grease jerks a thumb at the humming wall outlets. 'Cyberdeck Fragment. The smaller the piece, the bigger the headache.'",
                    'ready': "Grease squints. 'That the fragment? Lay it on the bar.'",
                    'success': "Grease pockets the fragment and slides you credits without a word. 'Drink's on you next time.'",
                    'completed': "Grease grins. 'Already paid out. Don't make me repeat myself.'",
                },
            },
            'doc kira': {
                'id': 'kira_stabilizer',
                'title': 'Stabilizer',
                'description': "Bring me an Adrenaline Shot. I'm running low and the street's getting rough.",
                'required_item': 'Adrenaline Shot',
                'reward_xp': 20,
                'reward_credits': 25,
                'dialog': {
                    'offer': "Doc Kira's hands are steady, but the clinic lights flicker. 'People are dropping faster than I can patch them. I need an Adrenaline Shot.'",
                    'accepted': "Kira nods once. 'Good. Bring it back sealed. If it's been tampered with, it could kill someone.'",
                    'reminder': "Kira's voice stays low. 'Adrenaline Shot. No substitutes.'",
                    'ready': "Kira's eyes sharpen. 'You have the shot? Hand it over.'",
                    'success': "Kira pockets the injector and exhales. 'You just bought someone another sunrise. Don't forget that.'",
                    'completed': "Kira gives you a tired smile. 'You did enough. Stay safe out there.'",
                },
            },
            'patch': {
                'id': 'patch_vr_chip',
                'title': 'Glitched VR Chip',
                'description': "Bring me a VR Chip. I want to inspect its firmware.",
                'required_item': 'VR Chip',
                'reward_xp': 20,
                'reward_credits': 30,
                'dialog': {
                    'offer': "Patch drums neon-painted nails on the terminal. 'Somebody's selling VR chips with a ghost in the code. I want to meet the ghost.'",
                    'accepted': "Patch smiles like a lock clicking open. 'Perfect. Bring me the chip and I'll tell you what it was really doing.'",
                    'reminder': "Patch tilts their head. 'VR Chip. Not a story, not a rumor - hardware.'",
                    'ready': "Patch's eyes flare with reflected UI. 'That's the chip? Let's crack it.'",
                    'success': "Patch pockets the chip and laughs softly. 'Oh, this is going to be fun. Here's your pay.'",
                    'completed': "Patch waves you off. 'Already got what I needed. Come back when you have stranger problems.'",
                },
            },
            'nyx': {
                'id': 'nyx_signal_jammer',
                'title': 'Signal Jammer',
                'description': "Bring me an EMP Grenade. Someone's sniffing my comms.",
                'required_item': 'EMP Grenade',
                'reward_xp': 30,
                'reward_credits': 45,
                'dialog': {
                    'offer': "Nyx leans close over the bassline. 'Someone's been listening. I need an EMP grenade - small storm, big silence.'",
                    'accepted': "Nyx flashes a razor smile. 'Good. When the lights stutter, we talk again.'",
                    'reminder': "Nyx's eyes scan the crowd. 'EMP Grenade. If you value your teeth, don't ask why.'",
                    'ready': "Nyx glances at the grenade and nods. 'Yeah. That'll do.'",
                    'success': "Nyx palms the device and slips you credits. 'No more ears on my line. Beautiful.'",
                    'completed': "Nyx raises a glass. 'Handled. Enjoy the noise.'",
                },
            },
            'cipher': {
                'id': 'cipher_red_eye',
                'title': 'Red Eye Sample',
                'description': "Score me a Vial of Red Eye. Quietly.",
                'required_item': 'Vial of Red Eye',
                'reward_xp': 30,
                'reward_credits': 60,
                'dialog': {
                    'offer': "Cipher's voice is a whisper behind a mask. 'Red Eye's flooding the alleys. I want a sample - untouched.'",
                    'accepted': "Cipher nods once. 'Smart. Don't get seen buying it. Don't get seen bringing it.'",
                    'reminder': "Cipher's eyes don't blink. 'Vial of Red Eye. Sealed.'",
                    'ready': "Cipher extends a gloved hand. 'Show me.'",
                    'success': "Cipher pockets the vial and the air feels colder. 'Good. Here's your money. Forget my face.'",
                    'completed': "Cipher turns away. 'We are done.'",
                },
            },
            'vera': {
                'id': 'vera_energy_drink',
                'title': 'Cold Energy',
                'description': "Bring me an Energy Drink from the street stalls.",
                'required_item': 'Energy Drink',
                'reward_xp': 10,
                'reward_credits': 15,
                'dialog': {
                    'offer': "Vera gestures at the flickering booths. 'Long shift. Short patience. Bring me an Energy Drink and I'll make it worth your time.'",
                    'accepted': "Vera nods. 'You're a lifesaver. Don't take the warm ones.'",
                    'reminder': "Vera sighs. 'Energy Drink. Cold. Please.'",
                    'ready': "Vera brightens. 'You found one? Give it here.'",
                    'success': "Vera cracks it open immediately. 'Perfect. Here - credits, and my gratitude.'",
                    'completed': "Vera smiles. 'Already paid. Thanks again.'",
                },
            },
        }
        # Dynamic mobs (e.g., roaming gangs) as counts per room
        self.mobs_by_room = {}
        # Define mob types with weights and base HP
        self.mob_types = [
            {'name': 'Street Punk', 'hp': 28, 'weight': 5},
            {'name': 'Cyber Thug', 'hp': 35, 'weight': 4},
            {'name': 'Gang Member', 'hp': 40, 'weight': 4},
            {'name': 'Blade Dancer', 'hp': 45, 'weight': 2},
            {'name': 'Corpo Security', 'hp': 50, 'weight': 2},
            {'name': 'Enforcer', 'hp': 55, 'weight': 1},
            {'name': 'Aug Bruiser', 'hp': 60, 'weight': 1},
            {'name': 'Drone Swarm', 'hp': 20, 'weight': 2},
            {'name': 'Net Runner', 'hp': 30, 'weight': 2}
        ]
        self._seed_roaming_gangs()

    def get_npcs(self, room_name):
        return list(self.npcs_by_room.get(room_name, []))

    def get_mission_for_npc(self, npc_name):
        if not npc_name:
            return None
        return self.missions_by_npc.get(str(npc_name).strip().lower())

    def get_mobs_in_room(self, room_name):
        # Return expanded list of mob names based on counts
        mobs = []
        counts = self.mobs_by_room.get(room_name, {})
        for name, cnt in counts.items():
            mobs.extend([name] * max(0, int(cnt)))
        return mobs

    def _street_rooms(self):
        # Consider these rooms as streets/alleys where gangs can roam
        return [r for r in self.rooms.keys() if any(
            key in r for key in (
                'plaza', 'avenue', 'street', 'alley', 'market', 'bazaar', 'neon_alley', 'scrapyard'
            )
        )]

    def _seed_roaming_gangs(self, count=8):
        import random
        streets = self._street_rooms()
        for _ in range(count):
            if not streets:
                break
            start = random.choice(streets)
            self.mobs_by_room.setdefault(start, {})
            # Weighted choice of mob type
            total = sum(m['weight'] for m in self.mob_types)
            r = random.uniform(0, total)
            upto = 0
            choice = self.mob_types[0]
            for m in self.mob_types:
                if upto + m['weight'] >= r:
                    choice = m
                    break
                upto += m['weight']
            name = choice['name']
            self.mobs_by_room[start][name] = self.mobs_by_room[start].get(name, 0) + 1

    def tick_roaming(self):
        # Move each gang member one step along a random available exit
        import random
        moves = []
        for room, counts in list(self.mobs_by_room.items()):
            for mob_name, count in list(counts.items()):
                for _ in range(int(count)):
                    exits = self.rooms.get(room, {}).get('exits', {})
                    if not exits:
                        continue
                    # Prefer to stay on street/alleys
                    dirs = list(exits.items())
                    random.shuffle(dirs)
                    next_room = None
                    for _, target in dirs:
                        if target in self._street_rooms():
                            next_room = target
                            break
                    if not next_room:
                        next_room = random.choice(list(exits.values()))
                    moves.append((room, next_room, mob_name))
        # Apply moves
        for src, dst, mob_name in moves:
            # decrement from src
            if self.mobs_by_room.get(src, {}).get(mob_name, 0) > 0:
                self.mobs_by_room[src][mob_name] -= 1
                if self.mobs_by_room[src][mob_name] <= 0:
                    del self.mobs_by_room[src][mob_name]
            # increment to dst
            self.mobs_by_room.setdefault(dst, {})
            self.mobs_by_room[dst][mob_name] = self.mobs_by_room[dst].get(mob_name, 0) + 1

    def take_mob(self, room_name, name):
        # Remove one mob instance by name from a room, if present
        if room_name in self.mobs_by_room and name in self.mobs_by_room[room_name]:
            self.mobs_by_room[room_name][name] -= 1
            if self.mobs_by_room[room_name][name] <= 0:
                del self.mobs_by_room[room_name][name]

    def get_shop_inventory(self, room_name):
        # Base catalog
        base = {
            'Stimpack': 50,
            'Energy Drink': 25,
            'Ammo': 25
        }
        # Per-venue additions/overrides
        per_room = {
            'rust_and_circuit': {
                'Stimpack': 50,
                'Energy Drink': 25,
                'Adrenaline Shot': 60
            },
            'data_leak': {
                'Encrypted Chip': 75,
                'VR Chip': 40
            },
            'night_market': {
                'Stimpack': 45,
                'Ammo': 25,
                'Armor Vest': 120,
                'EMP Grenade': 90
            },
            'black_market_bazaar': {
                'Holo Cloak': 300,
                'Neon Blade': 500,
                'Katana': 350
            },
            'club_nexus': {
                'Adrenaline Shot': 60,
                'Energy Drink': 25
            },
            'holo_dive': {
                'VR Chip': 40
            },
            'corporate_lobby': {
                'Visitor Pass': 20
            }
        }
        inv = dict(base)
        if room_name in per_room:
            inv.update(per_room[room_name])
        return inv

    def describe_room(self, room_name):
        room = self.rooms.get(room_name)
        if not room:
            return "You are in a void."
        desc = room['description']
        exits = ', '.join(room['exits'].keys())
        return f"{desc}\nExits: {exits}"

    def move_player(self, player, direction):
        current = self.rooms.get(player.current_room)
        if not current or direction not in current['exits']:
            return "You can't go that way."
        player.current_room = current['exits'][direction]
        return self.describe_room(player.current_room)
