ROLES = {
    "impostor": {"name": "🎭 Impostor", "team": "impostor"},
    "detective": {"name": "🕵️ Detective", "team": "players"},
    "analyst": {"name": "🧠 Analyst", "team": "players"},
    "witness": {"name": "👁️ Witness", "team": "players"},
    "survivor": {"name": "🛡️ Survivor", "team": "players"},
}

ACTIONS = {
    "investigate": "🔍 Investigate",
    "cctv": "👁️ Watch CCTV",
    "search": "🧩 Search Room",
    "trust": "🤝 Trust Someone",
    "secure": "🛡️ Secure Yourself",
    "sabotage": "⚠️ Sabotage",
}

SCENARIO = {
    "title": "THE LAST ROOM",
    "intro": (
        "A blackout has sealed everyone inside the facility.\n"
        "One person is secretly working against the group.\n"
        "Everyone has a fragment of the truth — nobody has the whole picture."
    ),
    "rounds": [
        {
            "title": "ROUND 1 — THE BLACKOUT",
            "story": "Emergency lights flicker. A locked terminal reports an unknown access event.",
        },
        {
            "title": "ROUND 2 — THE RECORDING",
            "story": "A damaged recording appears. Someone's voice is missing from the official log.",
        },
        {
            "title": "ROUND 3 — THE LAST ROOM",
            "story": "The final door opens. One decision will determine who leaves.",
        },
    ],
}
