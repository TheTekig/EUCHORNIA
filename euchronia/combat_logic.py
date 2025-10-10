from euchronia.models import HitResult
from random import choices,random,randint
import euchronia.game_logic as gl

#region   Calculate Base Functions

def _action_time(Hero, Enemy):
    """ """
    combat = [Hero, Enemy]
    limit = 100

    while True:
        for fighter in combat:
            lucky = randint(-2, 10)
            fighter.action_time += fighter.speed + lucky
            if fighter.action_time >= limit:
                fighter.action_time -= limit
                return fighter
        
def _calculate_precision(precision):
    """ """

    Results = [HitResult.MISS, HitResult.SCRATCH, HitResult.HIT]

    hit_chance = precision
    scratch_chance = (1.0 - hit_chance) * 0.7
    miss_chance = (1.0 - hit_chance) * 0.3

    weights = [miss_chance, scratch_chance, hit_chance]
    return choices(Results, weights=weights, k=1)[0]

def _calculate_damage(defender, damage, skill_effect):
    """ """
    
    defense_reduction_percent = defender.defense * (1 - skill_effect.get("defense_ignore", 0))
    defense_reduction_percent = defense_reduction_percent / (defense_reduction_percent + 100)
    damage = damage * (1 - defense_reduction_percent)

    return max(1, int(damage))

#endregion

#region   Skills Functions

def _attack_skill(attacker, defender, skill_data):
    """ """
    skill_effect = skill_data.get("effect", {})
    damage = attacker.strength * skill_effect.get('damage_multiplier', 1.0)

    if random() < skill_effect.get('critical_chance', 0):
        damage *= 2
    
    accuracy = _calculate_precision(skill_data.get('precision', 1.0))

    match accuracy:
        case HitResult.MISS:
            return "MISS"

        case HitResult.SCRATCH:
            damage *= 0.5
            damage = _calculate_damage(defender, damage, skill_effect)
            defender.take_damage(damage)
            return "Half Damage"

        case HitResult.HIT:
            damage = _calculate_damage(defender, damage, skill_effect)
            defender.take_damage(damage)
            return "Full Damage"
        
def _buff_skill(attacker, skill_data):
    """ """
    skill_effect = skill_data.get("effect", {})
    
    duration = skill_data.get('duration', 0)
    applied_effect = {}

    if "defense_multiplier" in skill_effect:
        applied_effect["defense_multiplier"] = skill_effect["defense_multiplier"] 
    if "strength_multiplier" in skill_effect:
        applied_effect["strength_multiplier"] = skill_effect["strength_multiplier"]
    if "speed_multiplier" in skill_effect:
        applied_effect["speed_multiplier"] = skill_effect["speed_multiplier"]
    
    if not applied_effect:
        return f"{attacker.name} tried to buff, but nothing happend!"
    
    attacker.apply_effect(
        name=f"Buff_{attacker.name}",
        data={"effect" : applied_effect, "duration" : duration}
    )

    return f"{attacker.name} got a buff during {duration} rounds!"

def _debuff_skill(defender, skill_data):
    """ """
    skill_effect = skill_data.get("effect", {})
    applied_effect = {}

    duration = skill_data.get("duration", 0)

    if "speed_reduce" in skill_effect:
         applied_effect["speed_reduce"] = skill_effect["speed_reduce"] 
    if "defense_reduce" in skill_effect:
         applied_effect["defense_reduce"] = skill_effect["defense_reduce"] 
    if "burn_chance" in skill_effect:
         applied_effect["damage_per_round"] = skill_effect.get("burn_damage", 5) 

    if not applied_effect:
        return
    
    defender.apply_effect(
        name=f"Debuff_{defender.name}",
        data={"effect" : applied_effect, "duration" : duration}
    )

    return  f"{defender} got a debuff during {duration} rounds"

def _control_skill(defender, skill_data):
    """ """
    skill_effect = skill_data.get("effect", {})
    freeze = skill_effect.get("freeze_chance", 1)

    duration = skill_data.get("duration", 0)

    if random() <= freeze:
        defender.apply_effect(
            name= "Freezed",
            data= {"effect" : {"lost_round" : True}, "duration" : duration} 
        )
        return f"{defender.name} got freeze"
    else:
        return f"{defender.name} resisted to freeze"

def _skill_manager(attacker, defensor, skill_data):
    """ """   

    skill_name = skill_data.get("name", "Unknow Attack")
    skill_type = skill_data.get("type", "ATTACK")

    if skill_type != "ATTACK":
        accuracy = _calculate_precision(skill_data.get("precision", 1))
        if accuracy == HitResult.MISS:
            return "MISS"

    match skill_type:
        case "ATTACK":
            return _attack_skill(attacker, defensor, skill_data)
        
        case "BUFF":
            return _buff_skill(attacker, skill_data)

        case "DEBUFF":
            return _debuff_skill(defensor, skill_data)
        
        case "CONTROL":
            return _control_skill(defensor, skill_data)
        case _: 
            return "INVALID"
        
#endregion 

def combat_loop(Hero, Enemy, Skills, items_data):
    
    while Hero.is_alive() and Enemy.is_alive():

        round = _action_time(Hero, Enemy)
        if "Freeze" in round.effect:
            if round == Hero:
                round = Enemy
            else:
                round = Hero
            
        
        if round == Hero:
                print("[S]kill [I]nventory [ST]atus [R]un")
                
                option = input(">> ")
                while option.upper() not in ["S", "I", "ST", "R"]:
                    option = input(">> ")

                match option.upper():
                    case "S":
                        print("Skills:")
                        skill_option = {}
                        for i, skill_name in enumerate(Hero.skills):
                            print(f"[{i+1}].{skill_name} / ", end="")
                            skill_option[str(i+1)] = skill_name

                        skill_choice = input(">> ")
                        while skill_choice not in skill_option:
                            skill_choice = input(">> ")
                            
                        selected_skill_option = skill_option[skill_choice]
                        action = _skill_manager(Hero, Enemy, Skills[selected_skill_option])
                        
                        print(action)

                    case "I":
                        gl.list_player_inventory(Hero)
                        gl.manage_inventory(Hero, items_data)

                    case "ST":
                        print("Status:")
                        Hero.status()

                    case "R":
                        print("Run")
                        return "You Runaway"
                    case _:
                        pass

        else:
                print("Enemy Turn")
                size = len(Enemy.skills)
                if size > 0:
                    skill_option = randint(0, size - 1)
                    skill_option = Enemy.skills[skill_option]
                    action = _skill_manager(Enemy, Hero, Skills[skill_option])
                    print(action)
                else:
                    skill_option = 0
                    action = _skill_manager(Enemy, Hero, Skills[skill_option])
                    print(action)
                    
                