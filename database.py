import sqlite3
import os
from pathlib import Path

DATABASE_NAME = "inven3.sqlite"
DATABASE_PATH = Path(__file__).parent.parent / DATABASE_NAME
VIEWS = {"Products": "/product", "Warehouses": "/location", "Logistics": "/movement"}
EMPTY_SYMBOLS = {"", " ", None}

def get_database_path():
    return os.environ.get("DATABASE_NAME") or DATABASE_PATH.resolve()

def init_database():
    PRODUCTS = ("products(prod_id INTEGER PRIMARY KEY AUTOINCREMENT, prod_name TEXT UNIQUE NOT NULL, prod_quantity INTEGER NOT NULL, unallocated_quantity INTEGER)")
    LOCATIONS = "location(loc_id INTEGER PRIMARY KEY AUTOINCREMENT, loc_name TEXT UNIQUE NOT NULL)"
    LOGISTICS = ("logistics(trans_id INTEGER PRIMARY KEY AUTOINCREMENT, prod_id INTEGER NOT NULL, from_loc_id INTEGER NULL, to_loc_id INTEGER NULL, prod_quantity INTEGER NOT NULL, trans_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(prod_id) REFERENCES products(prod_id), FOREIGN KEY(from_loc_id) REFERENCES location(loc_id), FOREIGN KEY(to_loc_id) REFERENCES location(loc_id))")

    with sqlite3.connect(get_database_path()) as conn:
        for table_definition in [PRODUCTS, LOCATIONS, LOGISTICS]:
            conn.execute(f"CREATE TABLE IF NOT EXISTS {table_definition}")
        conn.execute("CREATE TRIGGER IF NOT EXISTS default_prod_qty_to_unalloc_qty AFTER INSERT ON products FOR EACH ROW WHEN NEW.unallocated_quantity IS NULL BEGIN UPDATE products SET unallocated_quantity = NEW.prod_quantity WHERE rowid = NEW.rowid; END")


