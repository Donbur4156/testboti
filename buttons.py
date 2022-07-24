import interactions as di
from interactions.ext.persistence import *

def button_plus(bot: di.Client, number: int):
    pers_id_plus = PersistentCustomID(
        cipher=bot,
        tag="but_plus",
        package=number + 1
    )
    button_plus = di.Button(
        style=di.ButtonStyle.SUCCESS,
        label="+",
        custom_id=str(pers_id_plus)
    )
    return button_plus

def button_min(bot: di.Client, number: int):
    pers_id_min = PersistentCustomID(
        cipher=bot,
        tag="but_min",
        package=number - 1
    )
    button_min = di.Button(
        style=di.ButtonStyle.SUCCESS,
        label="-",
        custom_id=str(pers_id_min)
    )
    return button_min
