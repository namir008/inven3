import json
import sqlite3
from collections import defaultdict
from flask import redirect, render_template, request, Flask
from database import get_database_path, VIEWS, EMPTY_SYMBOLS

inven3 = Flask(__name__)

DATABASE_NAME = get_database_path()

# Route to display summary of warehouses, products, and quantities
@inven3.route("/", methods=["GET"])
def summary():
    with sqlite3.connect(DATABASE_NAME) as conn:
        warehouse = conn.execute("SELECT * FROM location").fetchall()
        products = conn.execute("SELECT * FROM products").fetchall()
        q_data = conn.execute(
            "SELECT prod_name, unallocated_quantity, prod_quantity FROM products"
        ).fetchall()

    return render_template(
        "index.jinja",
        link=VIEWS,
        title="Summary",
        warehouses=warehouse,
        products=products,
        summary=q_data,
    )


# Route to handle product creation and display existing products
@inven3.route("/product", methods=["POST", "GET"])
def product():
    with sqlite3.connect(DATABASE_NAME) as conn:
        if request.method == "POST":
            prod_name = request.form["prod_name"]
            quantity = request.form["prod_quantity"]

            if prod_name not in EMPTY_SYMBOLS and quantity not in EMPTY_SYMBOLS:
                conn.execute(
                    "INSERT INTO products (prod_name, prod_quantity) VALUES (?, ?)",
                    (prod_name, quantity),
                )
                return redirect(VIEWS["Stock"])

        products = conn.execute("SELECT * FROM products").fetchall()

    return render_template(
        "product.jinja",
        link=VIEWS,
        products=products,
        title="Stock",
    )


# Route to handle location (warehouse) creation and display existing locations
@inven3.route("/location", methods=["POST", "GET"])
def location():
    with sqlite3.connect(DATABASE_NAME) as conn:
        if request.method == "POST":
            warehouse_name = request.form["warehouse_name"]

            if warehouse_name not in EMPTY_SYMBOLS:
                conn.execute("INSERT INTO location (loc_name) VALUES (?)", (warehouse_name,))
                return redirect(VIEWS["Warehouses"])

        warehouse_data = conn.execute("SELECT * FROM location").fetchall()

    return render_template(
        "location.jinja",
        link=VIEWS,
        warehouses=warehouse_data,
        title="Warehouses",
    )


# Helper function to gather warehouse data based on product and location IDs
def get_warehouse_data(conn: sqlite3.Connection, products: list[tuple], locations: list[tuple]) -> list[tuple]:
    log_summary = []
    for p_id in [x[0] for x in products]:
        prod_name = conn.execute(
            "SELECT prod_name FROM products WHERE prod_id = ?", (p_id,)
        ).fetchone()

        for l_id in [x[0] for x in locations]:
            loc_name = conn.execute(
                "SELECT loc_name FROM location WHERE loc_id = ?", (l_id,)
            ).fetchone()
            sum_to_loc = conn.execute(
                "SELECT SUM(log.prod_quantity) FROM logistics log WHERE log.prod_id = ? AND log.to_loc_id = ?",
                (p_id, l_id),
            ).fetchone()
            sum_from_loc = conn.execute(
                "SELECT SUM(log.prod_quantity) FROM logistics log WHERE log.prod_id = ? AND log.from_loc_id = ?",
                (p_id, l_id),
            ).fetchone()

            log_summary.append(
                prod_name + loc_name + ((sum_to_loc[0] or 0) - (sum_from_loc[0] or 0),)
            )

    return log_summary


# Helper function to update warehouse data for product movement
def update_warehouse_data(conn: sqlite3.Connection):
    prod_name = request.form["prod_name"]
    from_loc = request.form["from_loc"]
    to_loc = request.form["to_loc"]
    quantity = request.form["quantity"]

    update_unallocated_quantity = False

    if from_loc in EMPTY_SYMBOLS:
        # Product is being shipped to a warehouse (initial condition)
        column_name = "to_loc_id"
        operation = "-"
        location_name = to_loc
        update_unallocated_quantity = True

    elif to_loc in EMPTY_SYMBOLS:
        # Product is unallocated (not shipped to any warehouse)
        column_name = "from_loc_id"
        operation = "+"
        location_name = from_loc
        update_unallocated_quantity = True

    else:
        # Product is being shipped between warehouses
        conn.execute(
            "INSERT INTO logistics (prod_id, from_loc_id, to_loc_id, prod_quantity) "
            "SELECT "
            "(SELECT prod_id FROM products WHERE prod_name = ?), "
            "(SELECT loc_id FROM location WHERE loc_name = ?), "
            "(SELECT loc_id FROM location WHERE loc_name = ?), ?",
            (prod_name, from_loc, to_loc, quantity),
        )

    if update_unallocated_quantity:
        conn.execute(
            f"INSERT INTO logistics (prod_id, {column_name}, prod_quantity) "
            "SELECT prod_id, loc_id, ? FROM products, location "
            "WHERE prod_name = ? AND loc_name = ?",
            (quantity, prod_name, location_name),
        )
        conn.execute(
            f"UPDATE products SET unallocated_quantity = unallocated_quantity {operation} ? WHERE prod_name = ?",
            (quantity, prod_name),
        )


# Route to handle product movement between warehouses
@inven3.route("/movement", methods=["POST", "GET"])
def movement():
    if request.method == "GET":
        with sqlite3.connect(DATABASE_NAME) as conn:
            logistics_data = conn.execute("SELECT * FROM logistics").fetchall()
            products = conn.execute("SELECT prod_id, prod_name, unallocated_quantity FROM products").fetchall()
            locations = conn.execute("SELECT loc_id, loc_name FROM location").fetchall()
            warehouse_summary = get_warehouse_data(conn, products, locations)
            item_location_qty_map = get_warehouse_map(warehouse_summary)

        return render_template(
            "movement.jinja",
            title="Logistics",
            link=VIEWS,
            products=products,
            locations=locations,
            allocated=item_location_qty_map,
            logistics=logistics_data,
            summary=warehouse_summary,
        )

    elif request.method == "POST":
        with sqlite3.connect(DATABASE_NAME) as conn:
            update_warehouse_data(conn)
        return redirect(VIEWS["Logistics"])


# Route to handle deletions (products or locations)
@inven3.route("/delete")
def delete():
    delete_record_type = request.args.get("type")

    with sqlite3.connect(DATABASE_NAME) as conn:
        if delete_record_type == "product":
            product_id = request.args.get("prod_id")
            if product_id:
                conn.execute("DELETE FROM products WHERE prod_id = ?", (product_id,))
            return redirect(VIEWS["Stock"])

        elif delete_record_type == "location":
            location_id = request.args.get("loc_id")
            if location_id:
                in_place = dict(
                    conn.execute(
                        "SELECT prod_id, SUM(prod_quantity) FROM logistics WHERE to_loc_id = ? GROUP BY prod_id",
                        (location_id,),
                    ).fetchall()
                )
                out_place = dict(
                    conn.execute(
                        "SELECT prod_id, SUM(prod_quantity) FROM logistics WHERE from_loc_id = ? GROUP BY prod_id",
                        (location_id,),
                    ).fetchall()
                )

                displaced_qty = in_place.copy()
                for x in in_place:
                    if x in out_place:
                        displaced_qty[x] -= out_place[x]

                for product_id, qty in displaced_qty.items():
                    conn.execute(
                        "UPDATE products SET unallocated_quantity = unallocated_quantity + ? WHERE prod_id = ?",
                        (qty, product_id),
                    )
                conn.execute("DELETE FROM location WHERE loc_id = ?", (location_id,))
            return redirect(VIEWS["Warehouses"])

        else:
            return redirect(VIEWS["Summary"])


# Route to handle edits (products or locations)
@inven3.route("/edit", methods=["POST"])
def edit():
    edit_record_type = request.args.get("type")

    with sqlite3.connect(DATABASE_NAME) as conn:
        if edit_record_type == "location":
            loc_id = request.form["loc_id"]
            loc_name = request.form["loc_name"]
            if loc_name:
                conn.execute(
                    "UPDATE location SET loc_name = ? WHERE loc_id = ?", (loc_name, loc_id)
                )
            return redirect(VIEWS["Warehouses"])

        elif edit_record_type == "product":
            prod_id = request.form["prod_id"]
            prod_name = request.form["prod_name"]
            prod_quantity = request.form["prod_quantity"]

            if prod_name:
                conn.execute(
                    "UPDATE products SET prod_name = ? WHERE prod_id = ?", (prod_name, prod_id)
                )
            if prod_quantity:
                old_prod_quantity = conn.execute(
                    "SELECT prod_quantity FROM products WHERE prod_id = ?", (prod_id,)
                ).fetchone()[0]
                conn.execute(
                    "UPDATE products SET prod_quantity = ?, unallocated_quantity = unallocated_quantity + ? - ? WHERE prod_id = ?",
                    (prod_quantity, prod_quantity, old_prod_quantity, prod_id),
                )
            return redirect(VIEWS["Stock"])

        else:
            return redirect(VIEWS["Summary"])

