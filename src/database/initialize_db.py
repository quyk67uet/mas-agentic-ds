import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def initialize_database():
    """Initialize the database with the schema"""
    try:
        # Connect to the database
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        cursor = conn.cursor()
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        schema_path = os.path.join(script_dir, 'schema.sql')
        
        with open(schema_path, 'r') as f:
            sql_script = f.read()
            
        cursor.execute(sql_script)
        
        conn.commit()
        
        print("Database initialized successfully")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    initialize_database() 