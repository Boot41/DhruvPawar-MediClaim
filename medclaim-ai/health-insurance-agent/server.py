# fastapi_server.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
import json

app = FastAPI()

DATABASE = 'insurance.db'

class Policy(BaseModel):
    policy_number: str
    user_id: str
    policyholder_name: str
    coverage_limit: int
    deductible: int
    copay_percentage: float
    coverage_types: list
    policy_status: str
    premium: int
    family_members: list

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.get('/policy/{policy_number}', response_model=Policy)
def get_policy(policy_number: str):
    conn = get_db_connection()
    policy_row = conn.execute('SELECT * FROM policies WHERE policy_number = ?', (policy_number,)).fetchone()
    conn.close()

    if policy_row is None:
        raise HTTPException(status_code=404, detail="Policy not found")

    policy = dict(policy_row)
    # Convert JSON strings back to Python objects
    policy['coverage_types'] = json.loads(policy['coverage_types'])
    policy['family_members'] = json.loads(policy['family_members'])
    return policy
