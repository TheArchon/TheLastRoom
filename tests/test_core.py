
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from game.roles import assign_roles


def test_role_assignment():
    players = list(range(4))
    roles = assign_roles(players)
    assert len(roles) == 4
    assert list(roles.values()).count("impostor") == 1
    assert list(roles.values()).count("detective") == 1
    assert list(roles.values()).count("analyst") == 1


def test_role_assignment_five_players():
    players = list(range(5))
    roles = assign_roles(players)
    assert len(roles) == 5
    assert list(roles.values()).count("impostor") == 1
    assert list(roles.values()).count("witness") == 1


def test_role_assignment_ten_players():
    players = list(range(10))
    roles = assign_roles(players)
    assert len(roles) == 10
    assert list(roles.values()).count("impostor") == 1
    assert list(roles.values()).count("detective") == 1
    assert list(roles.values()).count("analyst") == 1
    assert list(roles.values()).count("witness") == 1
    assert list(roles.values()).count("survivor") == 6
