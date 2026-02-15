import random


def handle_command(command, player, world, accounts=None, save_accounts=None):
    # Search command for loot after fights
    if command == 'search':
        if hasattr(player, 'last_defeated') and player.last_defeated:
            loot_table = [
                'Stimpack', 'Neon Blade', 'Cyberdeck Fragment', '50 credits', 'Red Eye Vial', 'Encrypted Chip', 'Energy Drink',
                'Ammo', 'EMP Grenade', 'VR Chip', 'Adrenaline Shot', 'Armor Vest'
            ]
            loot = random.choice(loot_table)
            if loot not in player.inventory:
                player.inventory.append(loot)
                msg = f"You search the {player.last_defeated} and find {loot}!"
            else:
                msg = f"You search the {player.last_defeated} but only find scraps."
            player.last_defeated = None
            return msg
        else:
            return "There's nothing to search here."
    if command in ("look", "l"):
        # Random encounter in hallway
        if player.current_room == "hall":
            # 20% chance for angry drug addict fight
            if random.random() < 0.2:
                player.in_fight = True
                player.fight_opponent = 'Angry Drug Addict'
                player.fight_hp = 30
                return world.describe_room(player.current_room) + "\n\nSuddenly, a wild-eyed drug addict lunges at you, fists swinging! You are in a fight! Type 'attack' to fight back or 'run' to try to escape."
            # Otherwise, normal random encounter
            encounter_chance = 0.5  # 50% chance
            encounters = [
                "A shadowy figure steps out and offers you a Vial of Red Eye.",
                "A cyber-rat scurries past your feet, carrying something shiny.",
                "A street dealer eyes you suspiciously, then vanishes into the darkness.",
                "You hear distant laughter and the flicker of neon lights intensifies.",
                "A drone buzzes overhead, scanning the hallway for movement."
            ]
            if random.random() < encounter_chance:
                encounter = random.choice(encounters)
                # Track if the encounter is the vial
                if 'vial' in encounter:
                    player.last_encounter = 'vial'
                else:
                    player.last_encounter = None
                return world.describe_room(player.current_room) + f"\n\n{encounter}"
            else:
                player.last_encounter = None
        return world.describe_room(player.current_room)
    # Fight logic for active battles (drug addict, roaming gangs, etc.)
    if hasattr(player, 'in_fight') and player.in_fight:
        if command == 'attack':
            # Damage now uses player's attack stat (strength + weapon bonus) with crits for Neon Blade
            base_roll = random.randint(6, 12)
            attack_stat = player.get_attack() if hasattr(player, 'get_attack') else getattr(player, 'strength', 10)
            weapon_bonus = 0
            neon_blade = getattr(player, 'equipment', {}).get('weapon') == 'Neon Blade'
            if neon_blade:
                weapon_bonus = 3
            # Crit chance: Neon Blade grants 15% crit for +50% damage
            crit = neon_blade and (random.random() < 0.15)
            dmg = base_roll + max(0, attack_stat // 4) + weapon_bonus
            if crit:
                dmg = int(dmg * 1.5)
            player.fight_hp -= dmg
            # Reduce endurance on attack
            player.endurance = max(0, getattr(player, 'endurance', 100) - random.randint(3, 7))
            if player.fight_hp <= 0:
                player.in_fight = False
                defeated = player.fight_opponent or 'opponent'
                player.fight_opponent = None
                player.fight_hp = None
                player.last_defeated = defeated
                xp_gain = random.randint(15, 30)
                player.xp = getattr(player, 'xp', 0) + xp_gain
                # Level up if needed
                if hasattr(player, 'xp_max') and player.xp >= player.xp_max:
                    player.level = getattr(player, 'level', 1) + 1
                    player.xp = player.xp - player.xp_max
                    player.xp_max = int(player.xp_max * 1.2) if hasattr(player, 'xp_max') else 100
                    level_msg = f"\nYou leveled up! You are now level {player.level}."
                else:
                    level_msg = ""
                return f"You strike with Atk {attack_stat} and deal {dmg} damage{' (CRIT!)' if crit else ''}! The {defeated} goes down. You win the fight!\nYou gain {xp_gain} XP.{level_msg}"
            else:
                # Opponent attacks back; scale by type
                foe = (getattr(player, 'fight_opponent', '') or '').strip()
                if foe in ('Aug Bruiser', 'Enforcer'):
                    opp_dmg = random.randint(8, 16)
                elif foe in ('Corpo Security', 'Blade Dancer', 'Gang Member'):
                    opp_dmg = random.randint(6, 13)
                elif foe in ('Street Punk', 'Cyber Thug', 'Drone Swarm', 'Net Runner'):
                    opp_dmg = random.randint(4, 10)
                else:
                    opp_dmg = random.randint(5, 12)
                player.hp = max(0, getattr(player, 'hp', 100) - opp_dmg)
                # Reduce willpower on taking damage
                player.willpower = max(0, getattr(player, 'willpower', 100) - random.randint(2, 6))
                msg = f"You attack (Atk {attack_stat}) and deal {dmg} damage{' (CRIT!)' if crit else ''}. He has {player.fight_hp} HP left.\nHe hits you back for {opp_dmg} damage!"
                if player.hp == 0:
                    player.in_fight = False
                    return msg + "\nYou were knocked out! You wake up later, dazed, with some health restored."
                return msg
        elif command == 'run':
            if random.random() < 0.5:
                player.in_fight = False
                player.fight_opponent = None
                player.fight_hp = None
                return "You manage to escape the drug addict and flee down the hallway!"
            else:
                opp_dmg = random.randint(5, 12)
                player.hp = max(0, getattr(player, 'hp', 100) - opp_dmg)
                msg = f"You try to run, but the drug addict grabs you and hits you for {opp_dmg} damage!"
                if player.hp == 0:
                    player.in_fight = False
                    return msg + "\nYou were knocked out! You wake up later, dazed, with some health restored."
                return msg

    elif command.startswith("take"):
        # Only allow taking the vial if the last encounter was the vial
        if hasattr(player, 'last_encounter') and player.last_encounter == 'vial':
            if 'Vial of Red Eye' not in player.inventory:
                player.inventory.append('Vial of Red Eye')
                player.last_encounter = None
                return "You take the Vial of Red Eye and add it to your inventory."
            else:
                return "You already have the Vial of Red Eye."
        else:
            # Generic take: allow players to pick up common items explicitly
            item = command[4:].strip()
            if not item:
                return "Take what?"
            # Normalize simple names
            proper = item.title()
            player.inventory.append(proper)
            return f"You take the {proper} and add it to your inventory."

    elif command.startswith("use "):
        item = command[4:].strip().lower()
        if item == "stimpack":
            # Consume Stimpack to restore health and endurance
            inv_name = next((i for i in player.inventory if i.lower() == 'stimpack'), None)
            if inv_name:
                player.inventory = [i for i in player.inventory if i != inv_name]
                player.hp = min(100, getattr(player, 'hp', 100) + 35)
                player.endurance = min(100, getattr(player, 'endurance', 100) + 25)
                return "You inject a Stimpack. Your health and endurance surge! (+35 HP, +25 END)"
            else:
                return "You don't have a Stimpack to use."
        if item == "vial of red eye":
            if 'Vial of Red Eye' in player.inventory:
                if not hasattr(player, 'red_eye_used') or not player.red_eye_used:
                    player.red_eye_used = True
                    player.attack_boost = 0.10
                    return "You consume the Vial of Red Eye. Your attack power increases by 10%!"
                else:
                    return "You've already used the Vial of Red Eye."
            else:
                return "You don't have a Vial of Red Eye to use."
        elif command == "mobs":
            # Diagnostics: list mobs in current and adjacent rooms
            here_counts = {}
            if hasattr(world, 'mobs_by_room'):
                here_counts = dict(world.mobs_by_room.get(player.current_room, {}))
            def fmt_counts(counts):
                if not counts:
                    return "None"
                return ", ".join([f"{name} x{int(cnt)}" for name, cnt in counts.items()])
            msg_lines = [f"Mobs here: {fmt_counts(here_counts)}"]
            exits = world.rooms.get(player.current_room, {}).get('exits', {}) if hasattr(world, 'rooms') else {}
            for dir_name, target in exits.items():
                adj_counts = {}
                if hasattr(world, 'mobs_by_room'):
                    adj_counts = dict(world.mobs_by_room.get(target, {}))
                if adj_counts:
                    msg_lines.append(f"{dir_name} -> {target}: {fmt_counts(adj_counts)}")
            return "\n".join(msg_lines)
        elif command == "spawn gang":
            # Diagnostics: spawn a Gang Member in the current room
            if hasattr(world, 'mobs_by_room'):
                world.mobs_by_room.setdefault(player.current_room, {})
                world.mobs_by_room[player.current_room]['Gang Member'] = world.mobs_by_room[player.current_room].get('Gang Member', 0) + 1
                return f"A Gang Member appears in {player.current_room}."
            else:
                return "Spawning mobs is not supported in this world."
    elif command.startswith("go "):
        direction = command[3:].strip()
        result = world.move_player(player, direction)
        # After moving, check for roaming gangs in the new room
        mobs_here = world.get_mobs_in_room(player.current_room) if hasattr(world, 'get_mobs_in_room') else []
        if mobs_here and random.random() < 0.5:
                player.in_fight = True
                # Pick one mob present for the encounter
                opp = random.choice(mobs_here)
                player.fight_opponent = opp
                # Determine HP by type defaults
                base_hp = 40
                if hasattr(world, 'mob_types'):
                    for mt in world.mob_types:
                        if mt['name'] == opp:
                            base_hp = mt.get('hp', base_hp)
                            break
                player.fight_hp = base_hp
                # remove one mob instance from the room to engage
                if hasattr(world, 'take_mob'):
                    world.take_mob(player.current_room, opp)
                return result + f"\n\nA {opp} spots you and rushes in! You're in a fight! Type 'attack' or 'run'."
        return result
    elif command.startswith("equip "):
        item_name = command[6:].strip()
        if not item_name:
            return "Specify an item to equip."
        # Simple slot mapping for known items
        slot_for_item = {
            'Neon Blade': 'weapon',
            'Katana': 'weapon',
            'Cyberdeck': 'hands',
            'Armor Vest': 'body',
            'Holo Cloak': 'accessory',
            'Stimpack': None,  # consumable, not equippable
            'Vial of Red Eye': None,
            'Ammo': None,
            'Energy Drink': None,
            'EMP Grenade': None,
            'Adrenaline Shot': None,
            'VR Chip': None,
            'Encrypted Chip': None,
            'Visitor Pass': None
        }
        # Find case-insensitive match in inventory
        inv_match = next((i for i in player.inventory if i.lower() == item_name.lower()), None)
        if not inv_match:
            return f"You don't have {item_name}."
        slot = slot_for_item.get(inv_match)
        if not slot:
            return f"{inv_match} cannot be equipped."
        # Equip: move from inventory to slot, unequip existing back to inventory
        if getattr(player, 'equipment', None) is None:
            player.equipment = {}
        prev = player.equipment.get(slot)
        player.equipment[slot] = inv_match
        player.inventory = [i for i in player.inventory if i != inv_match]
        if prev:
            player.inventory.append(prev)
        # Minimal stat adjustments
        if slot == 'weapon' and inv_match == 'Neon Blade':
            player.strength = getattr(player, 'strength', 10) + 2
        if slot == 'hands' and inv_match == 'Cyberdeck':
            player.tech = getattr(player, 'tech', 10) + 2
        return f"You equip {inv_match} on your {slot}."
    elif command.startswith("unequip "):
        slot = command[8:].strip().lower()
        if not slot:
            return "Specify a slot to unequip (e.g., weapon)."
        valid_slots = {'head','body','legs','feet','hands','weapon','offhand','accessory'}
        if slot not in valid_slots:
            return "Invalid slot. Try weapon, hands, head, body, legs, feet, offhand, accessory."
        if getattr(player, 'equipment', None) is None:
            player.equipment = {}
        item = player.equipment.get(slot)
        if not item:
            return f"Nothing equipped on {slot}."
        # Reverse minimal stat adjustments
        if slot == 'weapon' and item == 'Neon Blade':
            player.strength = max(1, getattr(player, 'strength', 10) - 2)
        if slot == 'hands' and item == 'Cyberdeck':
            player.tech = max(1, getattr(player, 'tech', 10) - 2)
        player.inventory.append(item)
        player.equipment[slot] = None
        return f"You unequip {item} from your {slot}."
    elif command.startswith("talk "):
        target = command[5:].strip().lower()
        if not target:
            return "Talk to whom?"
        npcs = world.get_npcs(player.current_room) if hasattr(world, 'get_npcs') else []
        if not npcs:
            return "No one seems interested in talking."
        # Find a matching NPC by name or role
        match = None
        for npc in npcs:
            if target in npc.get('name','').lower() or target in npc.get('role','').lower():
                match = npc
                break
        if not match:
            names = ', '.join([n['name'] for n in npcs])
            return f"You don't see {target}. NPCs here: {names}"
        role = match.get('role','')
        if role in ('Bartender','Vendor','Fence','Attendant'):
            return f"{match['name']} ({role}): 'For sale — try: shop'"
        elif role in ('Receptionist','Concierge'):
            return f"{match['name']} ({role}) nods politely. 'Welcome. Mind the security drones.'"
        elif role == 'DJ':
            return f"{match['name']} (DJ) barely hears you over the bass. Lights flare in response."
        else:
            return f"{match['name']} ({role}) acknowledges you with a curt nod."
    elif command.startswith("buy "):
        item_raw = command[4:].strip()
        item = item_raw.lower()
        npcs = world.get_npcs(player.current_room) if hasattr(world, 'get_npcs') else []
        vendor_here = any(n.get('role') in ('Bartender','Vendor','Fence','Attendant') for n in npcs)
        if not vendor_here:
            return "No one's selling here. Try a bar or the market."
        catalog = world.get_shop_inventory(player.current_room) if hasattr(world, 'get_shop_inventory') else {
            'Stimpack': 50,
            'Energy Drink': 25,
            'Ammo': 25
        }
        # Case-insensitive lookup
        price = None
        proper = None
        for name, p in catalog.items():
            if name.lower() == item:
                price = p
                proper = name
                break
        if price is None:
            return "They don't sell that here. Try 'shop'."
        if getattr(player, 'credits', 0) < price:
            return f"You need {price} credits to buy that."
        player.credits = getattr(player, 'credits', 0) - price
        player.inventory.append(proper)
        return f"You buy a {proper} for {price} credits."
    elif command == 'shop':
        npcs = world.get_npcs(player.current_room) if hasattr(world, 'get_npcs') else []
        vendor_here = any(n.get('role') in ('Bartender','Vendor','Fence','Attendant') for n in npcs)
        if not vendor_here:
            return "No shop here. Try a bar or vendor stall."
        catalog = world.get_shop_inventory(player.current_room) if hasattr(world, 'get_shop_inventory') else {
            'Stimpack': 50,
            'Energy Drink': 25,
            'Ammo': 25
        }
        items = ', '.join([f"{k} ({v} cr)" for k,v in catalog.items()])
        bal = getattr(player, 'credits', 0)
        return f"For sale: {items}. You have {bal} credits. Use 'buy <item>'."
    elif command == 'credits':
        return f"You have {getattr(player, 'credits', 0)} credits."
    elif command.startswith("name "):
        new_name = command[5:].strip()
        if not new_name:
            return "Please provide a new character name."
        if len(new_name) > 24:
            return "Name too long (max 24 characters)."
        player.name = new_name
        # Persist to account data if possible
        if accounts is not None and save_accounts is not None and hasattr(player, 'username'):
            acc = accounts.get(player.username)
            if acc is not None:
                acc['char_name'] = new_name
                save_accounts(accounts)
        return f"Character name changed to {new_name}."
    elif command in ("quit", "exit"):
        return "Goodbye!"
    else:
        return "Unknown command. Try 'look', 'go <direction>', 'equip <item>', 'unequip <slot>', or 'name <newname>'."