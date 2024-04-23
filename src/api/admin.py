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
        update_query = sqlalchemy.text("""
            UPDATE global_inventory
            SET red_ml = :newRedMl,
            blue_ml = :newBlueMl,
            green_ml = :newGreenMl,
            dark_ml = :newDarkMl,
            ml_threshold = :newMlThreshold,
            ml_capacity = :newMlCapacity,
            potion_capacity = :newPotionCapacity,
            potion_count = :newPotionCount,
            gold = :newGold
        """)

        connection.execute(update_query, {
            "newRedMl": 0,
            "newBlueMl": 0,
            "newGreenMl": 0,
            "newDarkMl": 0,
            "newMlThreshold": 5000,
            "newMlCapacity": 10000,
            "newPotionCapacity": 50,
            "newPotionCount": 0,
            "newGold": 100
        })

        query = sqlalchemy.text("""
            UPDATE potion_types
            SET quantity = :empty
        """)
        connection.execute(query, {
            "empty": 0
        })
    return "OK"

