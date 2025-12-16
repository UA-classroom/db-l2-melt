import os

import db
import psycopg2
import schemas
from db_setup import get_connection
from fastapi import FastAPI, HTTPException

app = FastAPI()

"""
ADD ENDPOINTS FOR FASTAPI HERE
Make sure to do the following:
- Use the correct HTTP method (e.g get, post, put, delete)
- Use correct STATUS CODES, e.g 200, 400, 401 etc. when returning a result to the user
- Use pydantic models whenever you receive user data and need to validate the structure and data types (VG)
This means you need some error handling that determine what should be returned to the user
Read more: https://www.geeksforgeeks.org/10-most-common-http-status-codes/
- Use correct URL paths the resource, e.g some endpoints should be located at the exact same URL, 
but will have different HTTP-verbs.
"""


# INSPIRATION FOR A LIST-ENDPOINT - Not necessary to use pydantic models, but we could to ascertain that we return the correct values
# @app.get("/items/")
# def read_items():
#     con = get_connection()
#     items = get_items(con)
#     return {"items": items}
@app.get("/presentations")
def read_presentations():
    conn = get_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Kunde inte koppla till databasen")
    
    try:
        # Här använder vi din funktion från db.py!
        results = db.get_all_presentations(conn)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close() # Jätteviktigt att stänga kopplingen
# 1. Skapa användare (Måste göras först!)
@app.post("/users")
def add_user(user: schemas.UserCreate):
    conn = get_connection()
    try:
        # Anropa funktionen i db.py
        user_id = db.create_user(conn, user.email, user.password_hash, user.avatar_url)
        conn.commit() # Spara ändringarna permanent
        return {"id": user_id, "message": "Användare skapad!"}
    except Exception as e:
        conn.rollback() # Ångra om något går fel
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

# 2. Skapa presentation
@app.post("/presentations")
def add_presentation(presentation: schemas.PresentationCreate):
    conn = get_connection()
    try:
        # Här skickar vi med owner_id som vi får från anropet
        new_id = db.create_presentation(conn, presentation.title, presentation.owner_id)
        conn.commit()
        return {"id": new_id, "message": "Presentation skapad!"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

# INSPIRATION FOR A POST-ENDPOINT, uses a pydantic model to validate
# @app.post("/validation_items/")
# def create_item_validation(item: ItemCreate):
#     con = get_connection()
#     item_id = add_item_validation(con, item)
#     return {"item_id": item_id}


# IMPLEMENT THE ACTUAL ENDPOINTS! Feel free to remove
