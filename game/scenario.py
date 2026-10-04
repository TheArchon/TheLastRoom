import random
from constants import SCENARIO


def action_clue(role, action, round_no, game):
    impostor_id = next((uid for uid, r in game["roles"].items() if r == "impostor"), None)
    names = game.get("names", {})
    if role == "impostor":
        clues = {
            "sabotage": "You found a way to corrupt the emergency log. Someone else may now look suspicious.",
            "cctv": "The camera feed has a 4-second blind spot. You know it was caused deliberately.",
            "search": "You found a broken access card. It can connect you to the terminal if exposed.",
            "secure": "You stayed hidden while the facility systems became less stable.",
        }
    else:
        clues = {
            "investigate": "The access event happened after someone entered a restricted corridor.",
            "cctv": "The CCTV timeline contains a short unexplained gap.",
            "search": "You found a damaged access card with no visible owner.",
            "trust": "Someone's story does not perfectly match the timing of the blackout.",
            "secure": "You protected your route and noticed movement nearby.",
        }
    clue = clues.get(action, "You noticed nothing conclusive.")
    if role == "detective" and action == "investigate" and impostor_id:
        clue += f"\n\n🔎 Strong lead: the suspicious activity is connected to <b>{names.get(str(impostor_id), 'an unknown player')}</b>."
    if role == "witness" and action == "cctv":
        clue += "\n\n👁️ Your memory says the missing footage began just before the alarm."
    if role == "analyst" and round_no >= 2:
        clue += "\n\n🧠 Pattern note: two public statements cannot both be true."
    return clue


def round_story(round_no):
    return SCENARIO["rounds"][round_no - 1]
