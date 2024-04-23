from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)


class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """ """
    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")
    with db.engine.begin() as connection:
        gold_paid = 0
        red_ml = 0
        blue_ml = 0
        green_ml = 0
        dark_ml = 0

        for barrel_delivered in barrels_delivered:
            gold_paid += barrel_delivered.price * barrel_delivered.quantity
            if barrel_delivered.potion_type == [1,0,0,0]:
                red_ml += barrel_delivered.ml_per_barrel * barrel_delivered.quantity
            elif barrel_delivered.potion_type == [0,1,0,0]:
                green_ml += barrel_delivered.ml_per_barrel * barrel_delivered.quantity
            elif barrel_delivered.potion_type == [0,0,1,0]:
                blue_ml += barrel_delivered.ml_per_barrel * barrel_delivered.quantity
            elif barrel_delivered.potion_type == [0,0,0,1]:
                dark_ml += barrel_delivered.ml_per_barrel * barrel_delivered.quantity
            else:
                raise Exception("Invalid potion type")

        connection.execute(
            sqlalchemy.text(
                """
                UPDATE global_inventory SET 
                red_ml = red_ml + :red_ml,
                green_ml = green_ml + :green_ml,
                blue_ml = blue_ml + :blue_ml,
                dark_ml = dark_ml + :dark_ml,
                gold = gold - :gold_paid
                """),
            [{"red_ml": red_ml, "green_ml": green_ml, "blue_ml": blue_ml, "dark_ml": dark_ml, "gold_paid": gold_paid}])
        
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)
    returnValue = {}

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("""
                                                     SELECT
                                                        green_ml,
                                                        blue_ml,
                                                        red_ml,
                                                        dark_ml,
                                                        gold,
                                                        ml_threshold,
                                                        ml_capacity
                                                        FROM global_inventory""")).one()
        
        ml_inventory = [result.red_ml, result.green_ml, result.blue_ml, result.dark_ml]
        ml_threshold = result.ml_threshold
        max_ml = result.ml_capacity
        current_ml = sum(ml_inventory)
        gold = result.gold
        barrel_purchases = []

        for i in range(len(ml_inventory)):
            if ml_inventory[i] < ml_threshold:
                potion_type = [int(j == i) for j in range(4)]
                barrel_available = next((item for item in wholesale_catalog if item.potion_type == potion_type), None)
                if barrel_available is not None:
                    if barrel_available.price <= gold and barrel_available.ml_per_barrel + current_ml <= max_ml:
                        price = barrel_available.price
                        ml_per_barrel = barrel_available.ml_per_barrel
                        barrel_info = {
                            "sku": barrel_available.sku,
                            "quantity": 1
                        }
                        barrel_purchases.append(barrel_info)
                        gold -= price
                        current_ml += ml_per_barrel
                

    return barrel_purchases

