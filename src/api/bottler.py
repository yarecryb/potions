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
        potion_types = connection.execute(sqlalchemy.text("SELECT * FROM potion_types"))
        for row in potion_types:
            sku = row.sku
            current_potion_type = [row.red_ml, row.green_ml, row.blue_ml, row.dark_ml]
            potion_bottled = next((item for item in potions_delivered if item.potion_type == current_potion_type), None)
            if potion_bottled is not None:
                connection.execute(
                    sqlalchemy.text(
                        """
                        UPDATE potion_types SET quantity = quantity + :quantity
                        WHERE sku = :potion_sku
                        """),
                [{"quantity": potion_bottled.quantity, "potion_sku": sku}])
                connection.execute(
                    sqlalchemy.text(
                        """
                        UPDATE global_inventory SET
                        red_ml = red_ml - :red_ml,
                        green_ml = green_ml - :green_ml,
                        blue_ml = blue_ml - :blue_ml,
                        dark_ml = dark_ml - :dark_ml,
                        potion_count = potion_count + :quantity
                        """),
                [{"red_ml": row.red_ml,
                  "green_ml": row.green_ml,
                  "blue_ml": row.blue_ml,
                  "dark_ml": row.dark_ml,
                  "quantity": potion_bottled.quantity}])
                
    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Bottle one of each potion
    returnValue = {}
    with db.engine.begin() as connection:
        inventory = connection.execute(sqlalchemy.text("""
                                                     SELECT
                                                        green_ml,
                                                        blue_ml,
                                                        red_ml,
                                                        dark_ml,
                                                        gold,
                                                        potion_count,
                                                        potion_capacity
                                                        FROM global_inventory""")).one()
        
        ml_inventory = [inventory.red_ml, inventory.green_ml, inventory.blue_ml, inventory.dark_ml]
        potion_count = inventory.potion_count
        potion_capacity = inventory.potion_capacity
        bottler_plan = []

        potion_types = connection.execute(sqlalchemy.text("SELECT * FROM potion_types"))
        for row in potion_types:
            current_potion_type = [row.red_ml, row.green_ml, row.blue_ml, row.dark_ml]
            create_potion = True
            for i in range(len(ml_inventory)):
                if ml_inventory[i] < current_potion_type[i]:
                    create_potion = False
                    break
            if potion_count+1 > potion_capacity:
                create_potion = False
            if create_potion:
                for i in range(len(ml_inventory)):
                    ml_inventory[i] = ml_inventory[i] - current_potion_type[i]

                bottler_plan.append({
                    "potion_type": current_potion_type,
                    "quantity": 1
                })
                potion_capacity +=1
        
    return bottler_plan

if __name__ == "__main__":
    print(get_bottle_plan())