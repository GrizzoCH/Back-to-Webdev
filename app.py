import sqlite3
import pandas as pd
import streamlit as st
from uuid import uuid4

DB_PATH = "data.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uuid TEXT UNIQUE,
                name TEXT,
                description TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                quantity INTEGER,
                FOREIGN KEY(product_id) REFERENCES products(id)
            )
            """
        )
        conn.commit()


def query_df(query, params=None):
    with get_connection() as conn:
        return pd.read_sql(query, conn, params=params or ())


def execute_sql(query, params=None):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        conn.commit()


def get_products():
    return query_df("SELECT id, uuid, name, description FROM products ORDER BY id")


def get_inventory():
    return query_df(
        """
        SELECT inventory.id,
               products.name AS product,
               inventory.quantity
        FROM inventory
        LEFT JOIN products ON inventory.product_id = products.id
        ORDER BY inventory.id
        """
    )


def create_product(name, description):
    execute_sql(
        "INSERT INTO products (uuid, name, description) VALUES (?, ?, ?)",
        (str(uuid4()), name.strip(), description.strip()),
    )


def update_product(product_id, name, description):
    execute_sql(
        "UPDATE products SET name = ?, description = ? WHERE id = ?",
        (name.strip(), description.strip(), product_id),
    )


def open_modal(label):
    try:
        return st.modal(label)
    except AttributeError:
        return st.expander(label, expanded=True)


def render_products_page():
    st.header("Products")
    st.write("Browse the product catalog. Use the popup forms to add or update products.")

    products = get_products()
    st.dataframe(products[['uuid', 'name', 'description']], use_container_width=True)

    if st.button("Add new product"):
        st.session_state.show_add_product_modal = True

    if products.empty:
        st.info("No products available yet.")
    else:
        choices = [f"{row.name} ({row.uuid[:8]})" for _, row in products.iterrows()]
        selected_index = st.selectbox("Select a product to edit", list(range(len(choices))), format_func=lambda i: choices[i])
        if st.button("Edit selected product"):
            selected_product = products.iloc[selected_index]
            st.session_state.edit_product_id = int(selected_product.id)
            st.session_state.show_edit_product_modal = True

    if st.session_state.get("show_add_product_modal", False):
        with open_modal("Add Product"):
            with st.form("add_product_form"):
                name = st.text_input("Product name")
                description = st.text_area("Description")
                submitted = st.form_submit_button("Create product")
                if submitted:
                    if not name.strip():
                        st.error("Product name cannot be empty.")
                    else:
                        create_product(name, description)
                        st.success("Product created.")
                        st.session_state.show_add_product_modal = False
                        st.experimental_rerun()

    if st.session_state.get("show_edit_product_modal", False):
        product_id = st.session_state.get("edit_product_id")
        product_row = products[products["id"] == product_id]
        if not product_row.empty:
            product_data = product_row.iloc[0]
            with open_modal("Edit Product"):
                with st.form("edit_product_form"):
                    name = st.text_input("Product name", value=product_data["name"])
                    description = st.text_area("Description", value=product_data["description"])
                    submitted = st.form_submit_button("Update product")
                    if submitted:
                        if not name.strip():
                            st.error("Product name cannot be empty.")
                        else:
                            update_product(product_id, name, description)
                            st.success("Product updated.")
                            st.session_state.show_edit_product_modal = False
                            st.experimental_rerun()
        else:
            st.session_state.show_edit_product_modal = False


def render_inventory_page():
    st.header("Inventory")
    st.write("Inventory is shown as a read-only table for quick review.")
    inventory = get_inventory()
    if inventory.empty:
        st.info("No inventory records found.")
    else:
        st.dataframe(inventory[['product', 'quantity']], use_container_width=True)


def main():
    st.set_page_config(page_title="Inventory App", layout="wide")
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Choose a page", ["Products", "Inventory"])

    init_db()

    if "show_add_product_modal" not in st.session_state:
        st.session_state.show_add_product_modal = False
    if "show_edit_product_modal" not in st.session_state:
        st.session_state.show_edit_product_modal = False
    if "edit_product_id" not in st.session_state:
        st.session_state.edit_product_id = None

    if page == "Products":
        render_products_page()
    else:
        render_inventory_page()


if __name__ == "__main__":
    main()
