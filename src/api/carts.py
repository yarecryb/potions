from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum
import sqlalchemy
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

    return {
        "previous": "",
        "next": "",
        "results": [
            {
                "line_item_id": 1,
                "item_sku": "1 oblivion potion",
                "customer_name": "Scaramouche",
                "line_item_total": 50,
                "timestamp": "2021-01-01T00:00:00Z",
            }
        ],
    }


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

carts = []
cartId = 0

@router.post("/")
def create_cart(new_cart: Customer):
    """ """
    global cartId
    # array of item sku, array of quantities
    cart = {
        "items": [],
        "quantities": [],
    }
    carts.append(cart)
    cartId += 1
    return {"cart_id": cartId}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    carts[cart_id-1]["items"].append(item_sku)
    carts[cart_id-1]["quantities"].append(cart_item.quantity)
    print(carts)
    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    total_potions_bought = 0
    total_gold_paid = 0
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        for row in result:
            cart = carts[cart_id-1]
            potion_count = cart["quantities"][cart_id-1]
            sku = cart["items"][cart_id-1]
            print(sku)
            if sku == "RED_POTION_0":
                total_potions_bought = potion_count
                new_potion_count = row[3] - potion_count
                update_query = sqlalchemy.text("UPDATE global_inventory SET num_red_potions = :new_potion_count")
                connection.execute(update_query, {"new_potion_count": new_potion_count})
                total_gold_paid = int(cart_checkout.payment)
                new_gold_amount = row[2] + total_gold_paid
                update_query = sqlalchemy.text("UPDATE global_inventory SET gold = :new_gold_amount")
                connection.execute(update_query, {"new_gold_amount": new_gold_amount})
            elif sku == "BLUE_POTION_0":
                total_potions_bought = potion_count
                new_potion_count = row[5] - potion_count
                update_query = sqlalchemy.text("UPDATE global_inventory SET num_blue_potions = :new_potion_count")
                connection.execute(update_query, {"new_potion_count": new_potion_count})
                total_gold_paid = int(cart_checkout.payment)
                new_gold_amount = row[2] + total_gold_paid
                update_query = sqlalchemy.text("UPDATE global_inventory SET gold = :new_gold_amount")
                connection.execute(update_query, {"new_gold_amount": new_gold_amount})
            elif sku == "GREEN_POTION_0":
                total_potions_bought = potion_count
                new_potion_count = row[0] - potion_count
                update_query = sqlalchemy.text("UPDATE global_inventory SET num_green_potions = :new_potion_count")
                connection.execute(update_query, {"new_potion_count": new_potion_count})
                total_gold_paid = int(cart_checkout.payment)
                new_gold_amount = row[2] + total_gold_paid
                update_query = sqlalchemy.text("UPDATE global_inventory SET gold = :new_gold_amount")
                connection.execute(update_query, {"new_gold_amount": new_gold_amount})
                
    return {"total_potions_bought": total_potions_bought, "total_gold_paid": total_gold_paid}
