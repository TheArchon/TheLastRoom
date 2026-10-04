import random
from constants import ROLES


def assign_roles(player_ids):
    n = len(player_ids)
    role_list = ["impostor", "detective", "analyst"]
    if n >= 5:
        role_list.append("witness")
    role_list += ["survivor"] * (n - len(role_list))
    random.shuffle(role_list)
    return {uid: role for uid, role in zip(player_ids, role_list)}


def role_message(role):
    data = ROLES[role]
    if role == "impostor":
        objective = "Hide your identity, create doubt, and survive the final vote."
    elif role == "detective":
        objective = "Read the clues and identify the Impostor."
    elif role == "analyst":
        objective = "Compare inconsistencies and help the group find the truth."
    elif role == "witness":
        objective = "Use your unique observations to expose contradictions."
    else:
        objective = "Survive and make the correct final decision."
    return (
        f"<b>Your role: {data['name']}</b>\n\n"
        f"<b>Objective:</b> {objective}\n\n"
        "Keep this message private. Your role and clues are not public."
    )
