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
    redPotionCount = 0
    bluePotionCount = 0
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        for row in result:
            greenPotionCount = row[0]
            redPotionCount = row[3]
            bluePotionCount = row[5]
            if greenPotionCount != 0:
                returnValue = {
                    "sku": "GREEN_POTION_0",
                    "name": "green potion",
                    "quantity": greenPotionCount,
                    "price": 50,
                    "potion_type": [0,100,0,0],
                }
            elif redPotionCount != 0:
                returnValue = {
                    "sku": "RED_POTION_0",
                    "name": "red potion",
                    "quantity": redPotionCount,
                    "price": 50,
                    "potion_type": [100,0,0,0],
                }
            elif bluePotionCount != 0:
                returnValue = {
                    "sku": "BLUE_POTION_0",
                    "name": "blue potion",
                    "quantity": bluePotionCount,
                    "price": 50,
                    "potion_type": [0,0,100,0],
                }
            
    if greenPotionCount == 0 or redPotionCount == 0 or bluePotionCount == 0:
        return []
    else:
        return [
                returnValue
            ]
