from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    returnValue = {}
    greenPotionCount = 0
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        for row in result:
            greenPotionCount = row[0]
            returnValue = {
                "sku": "GREEN_POTION_0",
                "name": "green potion",
                "quantity": greenPotionCount,
                "price": 10,
                "potion_type": [0,100,0,0],
            }
    if greenPotionCount == 0:
        return []
    else:
        return [
                returnValue
            ]
