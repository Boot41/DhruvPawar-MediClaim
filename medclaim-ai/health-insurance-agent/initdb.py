# init_db.py
import sqlite3
import json

conn = sqlite3.connect('insurance.db')
cursor = conn.cursor()

# Create table
cursor.execute('''
CREATE TABLE IF NOT EXISTS policies (
    policy_number TEXT PRIMARY KEY,
    user_id TEXT,
    policyholder_name TEXT,
    coverage_limit INTEGER,
    deductible INTEGER,
    copay_percentage REAL,
    coverage_types TEXT,
    policy_status TEXT,
    premium INTEGER,
    family_members TEXT
)
''')

# Insert sample data
sample_policy = {
    'policy_number': 'POL123456',
    'user_id': 'user001',
    'policyholder_name': 'John Doe',
    'coverage_limit': 500000,
    'deductible': 2500,
    'copay_percentage': 20.0,
    'coverage_types': json.dumps(['hospitalization', 'outpatient', 'prescription', 'diagnostic']),
    'policy_status': 'active',
    'premium': 1200,
    'family_members': json.dumps(['John Doe', 'Jane Doe'])
}

cursor.execute('''
INSERT OR REPLACE INTO policies VALUES (:policy_number, :user_id, :policyholder_name, :coverage_limit,
:deductible, :copay_percentage, :coverage_types, :policy_status, :premium, :family_members)
''', sample_policy)

conn.commit()
conn.close()
