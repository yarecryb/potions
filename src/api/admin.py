from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        update_query = sqlalchemy.text("""
            UPDATE global_inventory
            SET num_red_ml = :newRedMl,
            num_red_potions = :newRedPotions,
            num_blue_ml = :newBlueMl,
            num_blue_potions = :newBluePotions,
            num_green_ml = :newGreenMl,
            num_green_potions = :newGreenPotions,
            gold = :newGold
        """)

        connection.execute(update_query, {
            "newRedMl": 0,
            "newRedPotions": 0,
            "newBlueMl": 0,
            "newBluePotions": 0,
            "newGreenMl": 0,
            "newGreenPotions": 0,
            "newGold": 100
        })
    return "OK"

