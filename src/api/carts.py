from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
from enum import Enum
import math

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
    field_dict = {
        "customer_name":"customer_name",
        "item_sku":"sku",
        "line_item_total":"gold",
        "timestamp":"time"
    }
    full_results = []
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(
            f"SELECT \
                carts_transactions.id as unique_id, \
                carts.customer_name, \
                potion_inventory.sku, \
                carts_transactions.quantity, \
                potion_inventory.cost * carts_transactions.quantity as gold, \
                carts.created_at as time \
                FROM \
                    carts \
                    JOIN carts_transactions ON carts.cart_id = carts_transactions.cart_id \
                    JOIN potion_inventory ON carts_transactions.sku = potion_inventory.sku \
                    WHERE potion_inventory.sku like :sku and customer_name like :customer \
                    ORDER BY {field_dict.get(sort_col)} {sort_order.name}"),
                    [
                        {
                            "sku":f"%{potion_sku}%",
                            "customer":f"%{customer_name}%",
                        }
                    ]
                    )
        for row in result:
            full_results += [{
                "line_item_id": row.unique_id,
                "item_sku": f"{row.quantity} {row.sku}",
                "customer_name": row.customer_name,
                "line_item_total": row.gold,
                "timestamp": row.time,
            }]
    if search_page == "" or search_page == "1":
        page = 1
    else:
        page = int(search_page)
    total = len(full_results)
    max_page = math.ceil(total / 5)

    current = (5*(page-1))
    next = min(5*page, total)

    prev_page = max(page - 1,1)
    next_page = min(page + 1, max_page)

    if prev_page == page:
        prev_str = ""
    else:
        prev_str = str(prev_page)

    if next_page == page:
        next_str = ""
    else:
        next_str = str(next_page)

    return {
        "previous": prev_str,
        "next": next_str,
        "results": full_results[current:next],
    }


class NewCart(BaseModel):
    customer: str

@router.post("/")
def create_cart(new_cart: NewCart):
    """ """
    print("Attempting to generate cart...")
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(f"INSERT INTO carts(customer_name) \
                                                      VALUES ('{new_cart.customer}') \
                                                      RETURNING cart_id"))
        cart_id = result.first()[0]
    print(f"Cart Generated with ID: {cart_id}")
    return {"cart_id": cart_id}

@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """
    return {}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(f"INSERT INTO carts_transactions(cart_id, sku, quantity) \
                                                      VALUES ({cart_id}, '{item_sku}', {cart_item.quantity})"))
    print(f"Added {cart_item.quantity} of {item_sku} to cart {cart_id}...")

    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    # this sucks, need to redo eventually
    total_quantity = 0
    total_cost = 0
    
    # update gold
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(
            "INSERT INTO stock_ledger (d_gold, description) \
            SELECT d_gold, :description as description \
            FROM \
                ( \
                SELECT carts_transactions.quantity * potion_inventory.cost as d_gold \
                FROM carts_transactions \
                JOIN potion_inventory on potion_inventory.sku = carts_transactions.sku \
                WHERE carts_transactions.cart_id = :cart_id \
                ) \
            as subquery \
            RETURNING d_gold;"), 
            [{
                'description':f"Checkout Cart {cart_id} with payment {cart_checkout.payment}",
                'cart_id':cart_id
            }])
        result_pot = connection.execute(sqlalchemy.text(
            "INSERT into potion_ledger (d_quan, potion_id, description) \
            SELECT (-1*carts_transactions.quantity) as d_quan, potion_inventory.id as potion_id, :description as description \
            FROM carts_transactions \
            JOIN potion_inventory on potion_inventory.sku = carts_transactions.sku \
            WHERE carts_transactions.cart_id = :cart_id \
            RETURNING d_quan"), 
            [{
                'description':f"Checkout Cart {cart_id}",
                'cart_id':cart_id
            }])
        total_cost = result.first()[0]
        
        for row in result_pot:
            total_quantity += (-1)*row[0]
    

        print(f"Cart ID {cart_id} purchased {total_quantity} potions and paid {total_cost} gold")

        return {"total_potions_bought": total_quantity, "total_gold_paid": total_cost}
