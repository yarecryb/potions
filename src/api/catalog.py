from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    catalog = []
    with db.engine.begin() as connection:
        potion_types = connection.execute(sqlalchemy.text("SELECT * FROM potion_types"))
        for row in potion_types:
            if row.quantity != 0:
                catalog.append(
                {
                    "sku": row.sku, 
                    "quantity": row.quantity,
                    "price": row.price,
                    "potion_type": [row.red_ml, row.blue_ml, row.green_ml, row.dark_ml]
                })
    return catalog
