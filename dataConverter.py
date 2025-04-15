import os

import sqlite3 
import json

from dotenv import load_dotenv
load_dotenv()

DB_PATH = os.environ.get("DB_PATH")
OUTPUT_DIRECTORY = "./data/"
conn = sqlite3.connect(DB_PATH)

if __name__ == "__main__":
    data_platform = [
        "BITHUMB",
        "COINONE",
        "GOPAX",
        "KORBIT",
        "UPBIT"
    ]
    
    conn = sqlite3.connect(DB_PATH, check_same_thread = False)
    cursor = conn.cursor()
    for platform in data_platform:
        cursor.execute(f"SELECT * from orderbook where exchange='{platform}'")
        cols = [desc[0] for desc in cursor.description]
        
        results = []
        for row in cursor.fetchall():
            results.append(
                dict(
                    zip(cols, row)
                )
            )
        
        json_data = json.dumps(results, ensure_ascii=False, indent=2)
        
        with open(f"{OUTPUT_DIRECTORY}{platform}.json", 'w', encoding='utf-8') as f:
            f.write(json_data)
    conn.close()