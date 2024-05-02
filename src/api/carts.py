from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum
import sqlalchemy
from sqlalchemy import select, join
from src import database as db

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)


class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """
   

    with db.engine.connect() as conn:
        metadata_obj = sqlalchemy.MetaData()
        cart_items = sqlalchemy.Table("cart_items", metadata_obj, autoload_with=conn)
        carts = sqlalchemy.Table("carts", metadata_obj, autoload_with=conn)
        potion_types = sqlalchemy.Table("potion_types", metadata_obj, autoload_with=conn)

        stmt = (
            sqlalchemy.select(
                cart_items.c.id,
                cart_items.c.item_sku,
                cart_items.c.quantity,
                cart_items.c.timestamp,
                cart_items.c.price,
                carts.c.customer_name
            ).select_from(
                join(
                    cart_items,
                    carts,
                    cart_items.c.cart_id == carts.c.id
                )
            )
        )
        
        if customer_name != "":
            stmt = stmt.where(carts.c.customer_name.ilike(f"%{customer_name}%"))
        
        if potion_sku != "":
            stmt = stmt.where(cart_items.c.item_sku.ilike(f"%{potion_sku}%"))
        
        
        if sort_order == "asc":
            stmt = stmt.order_by(sqlalchemy.asc(sort_col))
        elif sort_order== "desc":
            stmt = stmt.order_by(sqlalchemy.desc(sort_col))

        result = conn.execute(stmt)
        json = {
            "previous": "", 
            "next": "", 
            "results": []
        }
        for row in result:
            json["results"].append(
                {
                    "line_item_id": row.id,
                    "item_sku": str(row.quantity) + " " + row.item_sku,
                    "customer_name": row.customer_name,
                    "line_item_total": row.price,
                    "timestamp": row.timestamp
                }
            )

    return json
    # return {
    #     "previous": "",
    #     "next": "",
    #     "results": [
    #         {
    #             "line_item_id": 1,
    #             "item_sku": "1 oblivion potion",
    #             "customer_name": "Scaramouche",
    #             "line_item_total": 50,
    #             "timestamp": "2021-01-01T00:00:00Z",
    #         }
    #     ],
    # }


class Customer(BaseModel):
    customer_name: str
    character_class: str
    level: int

@router.post("/visits/{visit_id}")
def post_visits(visit_id: int, customers: list[Customer]):
    """
    Which customers visited the shop today?
    """
    print(customers)

    return "OK"


@router.post("/")
def create_cart(new_cart: Customer):
    """ """
    cart_id = 0
    with db.engine.begin() as connection:
        cart_id = connection.execute(sqlalchemy.text(
            """
            INSERT INTO carts (customer_name, character_class, level)
            VALUES (:customer_name, :character_class, :level)
            RETURNING id
            """), [{"customer_name": new_cart.customer_name, "character_class": new_cart.character_class, "level": new_cart.level}])

    return {"cart_id": cart_id.fetchone()[0]}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    with db.engine.begin() as connection:
        existing_item = connection.execute(sqlalchemy.text(
            """
            SELECT * FROM cart_items
            WHERE cart_id = :cart_id AND item_sku = :item_sku
            """
        ), {"cart_id": cart_id, "item_sku": item_sku}).fetchone()

        if existing_item:
            connection.execute(sqlalchemy.text(
                """
                UPDATE cart_items
                SET quantity = :quantity
                WHERE cart_id = :cart_id AND item_sku = :item_sku
                """
            ), {"quantity": cart_item.quantity, "cart_id": cart_id, "item_sku": item_sku})
        else:
            connection.execute(sqlalchemy.text(
                """
                INSERT INTO cart_items (cart_id, item_sku, quantity)
                VALUES (:cart_id, :item_sku, :quantity)
                """
            ), {"cart_id": cart_id, "item_sku": item_sku, "quantity": cart_item.quantity})

    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    total_potions_bought = 0
    total_gold_paid = 0
    with db.engine.begin() as connection:
        items = connection.execute(sqlalchemy.text(
            """
            SELECT cartitem.item_sku, cartitem.quantity, potiontype.price
            FROM cart_items cartitem
            JOIN potion_types potiontype ON cartitem.item_sku = potiontype.sku
            WHERE cartitem.cart_id = :cart_id
            """
        ), {"cart_id": cart_id})


        for row in items:
            item_sku = row.item_sku
            quantity = row.quantity
            price = row.price

            connection.execute(sqlalchemy.text(
                """
                UPDATE potion_types
                SET quantity = quantity - :quantity
                WHERE sku = :item_sku
                """
            ), {"quantity": quantity, "item_sku": item_sku})

            gold_paid = quantity * price
            total_gold_paid += gold_paid

            connection.execute(sqlalchemy.text(
                """
                UPDATE cart_items
                SET price = :price
                WHERE cart_id = :cart_id AND item_sku = :item_sku
                """
            ), {"price": gold_paid, "cart_id": cart_id, "item_sku": item_sku})

            connection.execute(sqlalchemy.text(
                """
                UPDATE global_inventory
                SET gold = gold + :gold_paid,
                potion_count = potion_count - :quantity
                """
            ), {"gold_paid": gold_paid, "quantity": quantity})

            total_potions_bought += quantity
            
            ledger_transaction_value = "Potions bought: " + item_sku + " Quantity: " + str(quantity) +  " Gold change: " + str(gold_paid)
            inventory_id = connection.execute(
                sqlalchemy.text(
                    """
                    INSERT INTO ledger_transactions (description) 
                    VALUES (:value)
                    RETURNING id
                    """),
                [{"value": ledger_transaction_value}])
            
            connection.execute(
                sqlalchemy.text(
                    """
                    INSERT INTO ledger (inventory_id, gold_change, potion_count_change)
                    VALUES
                    (:inventory_id, :gold_change, :potion_count_change)
                    """
                ),
            [{"inventory_id": inventory_id.fetchone()[0], "gold_change": gold_paid, "potion_count_change": -quantity}])
                    
    return {"total_potions_bought": total_potions_bought, "total_gold_paid": total_gold_paid}
