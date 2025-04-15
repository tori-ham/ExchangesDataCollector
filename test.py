import os
from dotenv import load_dotenv
load_dotenv()

DB_PATH = os.environ.get("DB_PATH")

if __name__ == "__main__":
    print(DB_PATH)
