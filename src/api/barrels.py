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

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)
    returnValue = {}

    # check there are less than 10 potions in inventory
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        for row in result:
            if row[0] < 10:
                itemToBuy ={}
                for item in wholesale_catalog:
                    if item.sku == "SMALL_GREEN_BARREL":
                        itemToBuy = item
                if itemToBuy and row[2] > int(itemToBuy.price):
                    returnValue["sku"] = itemToBuy.sku
                    returnValue["quantity"] = 1

                    newGoldBalance = row[2] - int(itemToBuy.price)
                    update_query = sqlalchemy.text("UPDATE global_inventory SET gold = :newGoldBalance")
                    connection.execute(update_query, {"newGoldBalance": newGoldBalance})

                    newGreenMl = row[1] + itemToBuy.ml_per_barrel
                    update_query = sqlalchemy.text("UPDATE global_inventory SET num_green_ml = :newGreenMl")
                    connection.execute(update_query, {"newGreenMl": newGreenMl})




    return [
        returnValue
    ]

