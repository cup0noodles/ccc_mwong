from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    return_list = []
    # Get count of Red Potions
    print("Delivering Catalog...")

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(
            "SELECT * FROM \
            ( \
            SELECT \
            potion_inventory.sku, \
            potion_inventory.type_red, \
            potion_inventory.type_green, \
            potion_inventory.type_blue, \
            potion_inventory.type_dark, \
            potion_inventory.cost, \
            SUM(d_quan) AS total, \
            potion_inventory.name \
            FROM potion_inventory \
            join potion_ledger on potion_ledger.potion_id = potion_inventory.id \
            GROUP BY potion_inventory.id \
            ) as q \
            WHERE total > 0 AND sku != 'null'\
            ORDER BY total desc"))
    for row in result:
        sku = row[0]
        red = row[1]
        green = row[2]
        blue = row[3]
        dark = row[4]
        cost = int(row[5])
        quantity = row[6]
        name = row[7]
        print(f"Catalog contains {quantity} {sku}...")
        return_list += [
                {
                    "sku": sku,
                    "name": f"{name}",
                    "quantity": quantity,
                    "price": cost,
                    "potion_type": [red,green,blue,dark],
                }
            ]

        if len(return_list) >= 6:
            break
    print("Current Catalog:")
    print(return_list)
    return return_list