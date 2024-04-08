from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    """ """
    print(f"potions delievered: {potions_delivered} order_id: {order_id}")

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        greenPotionCount = 0
        for potion in potions_delivered:
            if potion.potion_type[1] == 100:
                greenPotionCount = potion.quantity
        if greenPotionCount != 0:
            for row in result:
                greenMl = row[1] - (greenPotionCount * 100)
                newGreenPotionCount = greenPotionCount+row[0]
                update_query = sqlalchemy.text("UPDATE global_inventory SET num_green_potions = :newGreenPotionCount")
                connection.execute(update_query, {"newGreenPotionCount": newGreenPotionCount})
                update_query = sqlalchemy.text("UPDATE global_inventory SET num_green_ml = :greenMl")
                connection.execute(update_query, {"greenMl": greenMl})

    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into green potions.
    returnValue = {}
    #bottle small green postions
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        for row in result:
            greenMl = row[1]
            greenPotionCount = 0
            while greenMl >= 100:
                returnValue["potion_type"] = [0,100,0,0]
                greenMl -= 100
                greenPotionCount += 1
            if greenPotionCount != 0:
                returnValue["quantity"] = greenPotionCount
            else:
                returnValue = {}   

    return [
            returnValue
        ]

if __name__ == "__main__":
    print(get_bottle_plan())