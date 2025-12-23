import random


def _recommended_mission_tier(player):
    try:
        level = int(getattr(player, 'level', 1) or 1)
    except Exception:
        level = 1
    try:
        hp = int(getattr(player, 'hp', 100) or 0)
    except Exception:
        hp = 100
    try:
        atk = int(player.get_attack()) if hasattr(player, 'get_attack') else int(getattr(player, 'strength', 10) or 10)
    except Exception:
        atk = 10

    # Minimal, deterministic heuristic (no gating): prefer easy early, hard late.
    if level <= 2 or atk <= 12 or hp <= 60:
        return 'easy'
    if level >= 7 and atk >= 16 and hp >= 85:
        return 'hard'
    return 'medium'


def _player_quests(player):
    quests = getattr(player, 'quests', None)
    if not isinstance(quests, dict):
        quests = {}
        try:
            player.quests = quests
        except Exception:
            pass
    return quests


def _persist_player_quests(player, accounts, save_accounts):
    if accounts is None or save_accounts is None:
        return
    username = getattr(player, 'username', None)
    if not username or username not in accounts:
        return
    try:
        accounts[username]['quests'] = dict(_player_quests(player))
        save_accounts(accounts)
    except Exception:
        return


def _find_npc_in_room(world, player, target_text):
    target = (target_text or '').strip().lower()
    if not target:
        return None
    npcs = world.get_npcs(player.current_room) if hasattr(world, 'get_npcs') else []
    for npc in npcs:
        if target == npc.get('name', '').lower() or target == npc.get('role', '').lower():
            return npc
        if target in npc.get('name', '').lower() or target in npc.get('role', '').lower():
            return npc
    return None


def _mission_state_for(player, mission_id):
    q = _player_quests(player).get(mission_id)
    if isinstance(q, dict):
        return q.get('status')
    return None

def handle_command(command, player, world, accounts=None, save_accounts=None):
    cmd = (command or '').strip()
    cmd_l = cmd.lower()

    if cmd_l in ('help', '?'):
        return (
            "Commands:\n\n"
            "Movement\n"
            "- look (l): Re-describe the current room.\n"
            "- go <north|south|east|west>: Move between rooms.\n"
            "- go out: Leave an instanced alley mission (when available).\n\n"
            "Combat\n"
            "- attack: Attack your current opponent (only in a fight).\n"
            "- run: Try to escape a fight.\n"
            "- search: Search after fights for loot (when available).\n\n"
            "Items & Gear\n"
            "- inventory: View your inventory (UI panel).\n"
            "- take <item>: Pick up an item (context-sensitive).\n"
            "- use <item>: Use a consumable (e.g., use stimpack).\n"
            "- equip <item>: Equip an item from your inventory.\n"
            "- unequip <slot>: Remove equipped item (weapon, hands, head, body, legs, feet, offhand, accessory).\n\n"
            "NPCs & Missions\n"
            "- talk <npc>: Talk and get mission offers/reminders.\n"
            "- accept <mission_id>: Accept the NPC mission in your current room.\n"
            "- turnin <mission_id>: Turn in an accepted mission when you have the required item.\n"
            "- quests: List your active/completed missions.\n\n"
            "Alley Runs (Instanced)\n"
            "- mission [easy|medium|hard]: Start a back-alley run (only from back alleys).\n"
            "- mission tiers: Show tiers + your recommended tier.\n"
            "- leave: Abort an active alley run and return to the city.\n\n"
            "Shops & Meta\n"
            "- shop: View items for sale (when a vendor is present).\n"
            "- buy <item>: Buy an item from a shop.\n"
            "- credits: Show your credit balance.\n"
            "- name <new_name>: Set your character name.\n"
            "- quit / exit: End your session."
        )

    # Mission instances: start only from back alleys
    if cmd.startswith('mission'):
        parts = cmd.split()
        tier = None
        if len(parts) > 1:
            tier = parts[1].strip().lower()
        if tier in ('tiers', 'help', '?'):
            rec = _recommended_mission_tier(player)
            try:
                lvl = int(getattr(player, 'level', 1) or 1)
            except Exception:
                lvl = 1
            return f"Mission tiers: easy, medium, hard. Use: mission <tier>\nRecommended for you: {rec} (level {lvl})"
        room = getattr(player, 'current_room', '')
        if 'back_alley' not in str(room):
            return "You can only start a mission from a back alley."
        if hasattr(world, 'get_instance_for_player') and world.get_instance_for_player(player):
            return "You're already in a mission instance. Use 'leave' to abort."
        if hasattr(world, 'start_mission_instance'):
            if tier not in (None, '', 'easy', 'medium', 'hard'):
                return "Unknown tier. Use: mission easy|medium|hard"
            out = world.start_mission_instance(player, entry_room=room, tier=tier)
            try:
                shown_tier = tier if tier not in (None, '') else 'recommended'
                player._last_world_event = {'text': f"Started a {shown_tier} alley run."}
            except Exception:
                pass
            if tier in (None, ''):
                rec = _recommended_mission_tier(player)
                try:
                    lvl = int(getattr(player, 'level', 1) or 1)
                except Exception:
                    lvl = 1
                tip = f"Tip: recommended tier for you is {rec} (level {lvl}). Start with `mission {rec}`.\n\n"
                return tip + out
            return out
        return "Missions are not supported in this world."

    if cmd == 'leave':
        inst = world.get_instance_for_player(player) if hasattr(world, 'get_instance_for_player') else None
        if not inst:
            return "You're not in a mission instance."
        entry = inst.get('entry_room')
        if hasattr(world, 'end_mission_instance'):
            world.end_mission_instance(player)
        if entry and hasattr(world, 'rooms') and entry in world.rooms:
            player.current_room = entry
            try:
                player._last_world_event = {'text': "Walked away from an alley run."}
            except Exception:
                pass
            return world.describe_room(entry, entering=True)
        try:
            player._last_world_event = {'text': "Walked away from an alley run."}
        except Exception:
            pass
        return "You leave the mission and return to the city."

    # Search command for loot after fights
    if cmd == 'search':
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
    if cmd in ("look", "l"):
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
        if cmd == 'attack':
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

                # Mission instance completion: if the defeated enemy is the instance boss
                inst = world.get_instance_for_player(player) if hasattr(world, 'get_instance_for_player') else None
                if inst and defeated == inst.get('boss'):
                    world.complete_mission_instance(player) if hasattr(world, 'complete_mission_instance') else None
                    bonus_xp = int(inst.get('reward_xp', 0) or 0)
                    bonus_cr = int(inst.get('reward_credits', 0) or 0)
                    player.xp = getattr(player, 'xp', 0) + bonus_xp
                    player.credits = getattr(player, 'credits', 0) + bonus_cr
                    title = inst.get('title', 'Mission')
                    try:
                        tier_txt = inst.get('tier') or ''
                        if tier_txt:
                            player._last_world_event = {'text': f"Cleared a {tier_txt} alley boss."}
                        else:
                            player._last_world_event = {'text': "Cleared an alley boss."}
                    except Exception:
                        pass
                    return (
                        f"You strike with Atk {attack_stat} and deal {dmg} damage{' (CRIT!)' if crit else ''}! The {defeated} goes down. You win the fight!\n"
                        f"MISSION COMPLETE: {title}! (+{bonus_cr} cr, +{bonus_xp} XP)\n"
                        "Type 'go out' to leave, or 'leave' to abort and clean up."
                    )

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
        elif cmd == 'run':
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
    elif cmd.startswith("go "):
        direction = command[3:].strip()
        result = world.move_player(player, direction)
        # After moving, check for roaming gangs in the new room
        mobs_here = world.get_mobs_in_room(player.current_room) if hasattr(world, 'get_mobs_in_room') else []
        if mobs_here:
            # 50% chance to get jumped if a mob is present (always in mission instances)
            force = hasattr(world, 'is_instance_room') and world.is_instance_room(player.current_room)
            if force or (random.random() < 0.5):
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
                # Scale boss HP for mission instances
                inst = world.get_instance_for_player(player) if hasattr(world, 'get_instance_for_player') else None
                if inst and opp == inst.get('boss'):
                    try:
                        base_hp = int(base_hp * float(inst.get('boss_hp_mult', 1.0) or 1.0))
                    except Exception:
                        pass
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
        slot = slot_for_item.get(inv_match, None)
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

        try:
            player._last_equip = {'action': 'equip', 'slot': slot, 'item': inv_match}
        except Exception:
            pass
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

        try:
            player._last_equip = {'action': 'unequip', 'slot': slot, 'item': item}
        except Exception:
            pass
        return f"You unequip {item} from your {slot}."
    elif command.startswith("talk "):
        target = command[5:].strip().lower()
        if not target:
            return "Talk to whom?"
        npcs = world.get_npcs(player.current_room) if hasattr(world, 'get_npcs') else []
        if not npcs:
            return "No one seems interested in talking."

        match = _find_npc_in_room(world, player, target)
        if not match:
            names = ', '.join([n['name'] for n in npcs])
            return f"You don't see {target}. NPCs here: {names}"

        role = match.get('role', '')
        npc_name = match.get('name', '')
        mission = world.get_mission_for_npc(npc_name) if hasattr(world, 'get_mission_for_npc') else None
        if mission:
            mid = mission.get('id')
            state = _mission_state_for(player, mid)
            req_item = mission.get('required_item')
            hint = mission.get('hint')
            hint_line = f"\nHint: {hint}" if hint else ""
            dialog = mission.get('dialog') if isinstance(mission.get('dialog'), dict) else {}
            if state == 'completed':
                completed_line = dialog.get('completed') or "We're square. Come back later."
                return f"{npc_name} ({role}): {completed_line}"
            if state == 'accepted':
                has_item = any((i or '').lower() == str(req_item).lower() for i in getattr(player, 'inventory', []))
                if has_item:
                    ready_line = dialog.get('ready') or "You got it? Hand it over."
                    return (
                        f"{npc_name} ({role}): {ready_line}\n"
                        f"Turn-in: {mission.get('title')} — type `turnin {mid}`"
                    )
                reminder_line = dialog.get('reminder') or f"{mission.get('title')}: {mission.get('description')}"
                return (
                    f"{npc_name} ({role}): {reminder_line}{hint_line}\n"
                    f"Need: {req_item}."
                )

            offer_line = dialog.get('offer') or f"{mission.get('title')}: {mission.get('description')}"
            return (
                f"{npc_name} ({role}): {offer_line}{hint_line}\n"
                f"Need: {req_item}. Reward: {mission.get('reward_credits', 0)} cr, {mission.get('reward_xp', 0)} XP.\n"
                f"Type `accept {mid}` to accept."
            )

        if role in ('Bartender', 'Vendor', 'Fence', 'Attendant'):
            return f"{npc_name} ({role}): 'For sale — try: shop'"
        if role in ('Receptionist', 'Concierge'):
            return f"{npc_name} ({role}) nods politely. 'Welcome. Mind the security drones.'"
        if role == 'DJ':
            return f"{npc_name} (DJ) barely hears you over the bass. Lights flare in response."
        return f"{npc_name} ({role}) acknowledges you with a curt nod."

    elif command == 'quests':
        quests = _player_quests(player)
        if not quests:
            return "You have no active missions. Try `talk <npc>` to find work."
        active = []
        done = []
        for mid, info in quests.items():
            if not isinstance(info, dict):
                continue
            title = info.get('title', mid)
            giver = info.get('giver', '?')
            status = info.get('status', 'accepted')
            line = f"{mid}: {title} (from {giver}) [{status}]"
            if status == 'completed':
                done.append(line)
            else:
                active.append(line)
        parts = []
        if active:
            parts.append("Active:\n" + "\n".join(active))
        if done:
            parts.append("Completed:\n" + "\n".join(done))
        return "\n\n".join(parts) if parts else "You have no active missions."

    elif command.startswith('accept '):
        token = command[7:].strip().lower()
        if not token:
            return "Accept what? Try `accept <mission_id>`."
        # Only allow accepting missions from NPCs in the current room
        npcs = world.get_npcs(player.current_room) if hasattr(world, 'get_npcs') else []
        available = []
        for npc in npcs:
            mission = world.get_mission_for_npc(npc.get('name')) if hasattr(world, 'get_mission_for_npc') else None
            if mission and mission.get('id'):
                available.append((npc, mission))
        chosen = None
        for npc, mission in available:
            mid = str(mission.get('id')).lower()
            if token == mid or token == str(npc.get('name', '')).lower():
                chosen = (npc, mission)
                break
        if not chosen:
            if not available:
                return "No missions available here. Try `talk <npc>` somewhere else."
            mids = ", ".join(sorted({m.get('id') for _, m in available}))
            return f"Unknown mission. Available here: {mids}"
        npc, mission = chosen
        mid = mission.get('id')
        state = _mission_state_for(player, mid)
        if state == 'completed':
            return "You already completed that mission."
        if state == 'accepted':
            return "You already accepted that mission."
        quests = _player_quests(player)
        quests[mid] = {
            'status': 'accepted',
            'giver': npc.get('name'),
            'title': mission.get('title', mid),
        }
        _persist_player_quests(player, accounts, save_accounts)
        dialog = mission.get('dialog') if isinstance(mission.get('dialog'), dict) else {}
        accepted_line = dialog.get('accepted')
        extra = f"Need: {mission.get('required_item')}."
        hint = mission.get('hint')
        hint_line = f"\nHint: {hint}" if hint else ""
        if accepted_line:
            return f"{npc.get('name')}: {accepted_line}\n{extra}{hint_line}"
        return f"Mission accepted: {mission.get('title')} ({extra}){hint_line}"

    elif command.startswith('turnin '):
        token = command[7:].strip().lower()
        if not token:
            return "Turn in what? Try `turnin <mission_id>`."
        quests = _player_quests(player)
        # Find mission from any NPC in this room
        npcs = world.get_npcs(player.current_room) if hasattr(world, 'get_npcs') else []
        available = []
        for npc in npcs:
            mission = world.get_mission_for_npc(npc.get('name')) if hasattr(world, 'get_mission_for_npc') else None
            if mission and mission.get('id'):
                available.append((npc, mission))
        chosen = None
        for npc, mission in available:
            mid = str(mission.get('id')).lower()
            if token == mid or token == str(npc.get('name', '')).lower():
                chosen = (npc, mission)
                break
        if not chosen:
            return "No matching mission to turn in here."
        npc, mission = chosen
        mid = mission.get('id')
        state = _mission_state_for(player, mid)
        if state != 'accepted':
            return "You haven’t accepted that mission yet."
        req_item = mission.get('required_item')
        inv = list(getattr(player, 'inventory', []))
        idx = next((i for i, it in enumerate(inv) if (it or '').lower() == str(req_item).lower()), None)
        if idx is None:
            return f"You still need: {req_item}."
        # Remove one required item, grant rewards
        inv.pop(idx)
        player.inventory = inv
        player.xp = int(getattr(player, 'xp', 0)) + int(mission.get('reward_xp', 0) or 0)
        player.credits = int(getattr(player, 'credits', 0)) + int(mission.get('reward_credits', 0) or 0)
        quests[mid] = {
            'status': 'completed',
            'giver': npc.get('name'),
            'title': mission.get('title', mid),
        }
        _persist_player_quests(player, accounts, save_accounts)
        dialog = mission.get('dialog') if isinstance(mission.get('dialog'), dict) else {}
        success_line = dialog.get('success')
        rewards = f"(+{int(mission.get('reward_credits', 0) or 0)} cr, +{int(mission.get('reward_xp', 0) or 0)} XP)"
        try:
            title = mission.get('title') or str(mid)
            player._last_world_event = {'text': f"Closed a contract: {title}."}
        except Exception:
            pass
        if success_line:
            return f"{npc.get('name')}: {success_line}\nMission complete: {mission.get('title')}! {rewards}"
        return f"Mission complete: {mission.get('title')}! {rewards}"
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