# File: internal-db.py
# Description: handles storage of pipeline status to display to user
#  
#
# Copyright (c) 2025 Michael Powers
#
# Usage: not to be run directly
#   
# 
#
import sqlite3
import datetime
import json 

DB_PATH = 'status.db'
PROCESS_TABLE_NAME = 'user_process_status'
RECOMMENDATIONS_TABLE_NAME = "recommendations"


def create_db_and_table(db_path=DB_PATH):
    """
    Creates the SQLite database file and the table to store user process status.
    The table will have a user_id as primary key and 8 status fields.
    """
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Define the table schema
        # user_id: Unique identifier for each user
        # field1 to field8: Text fields to store the status of each progress step
        # last_updated: Timestamp of the last update
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {PROCESS_TABLE_NAME} (
            user_id TEXT PRIMARY KEY,
            user_question TEXT DEFAULT 'Not started',
            cleaned_question TEXT DEFAULT 'Not started',
            tables 'Not started',
            joins 'Not started',
            grouping TEXT DEFAULT 'Not started',
            calculations TEXT DEFAULT 'Not started',
            filtering TEXT DEFAULT 'Not started',
            sql TEXT DEFAULT 'Not started',
            field8 TEXT DEFAULT 'Not started',
            last_updated TEXT
        );
        """
        cursor.execute(create_table_sql)
        conn.commit()
        print(f"Database '{db_path}' and table '{PROCESS_TABLE_NAME}' ensured to exist.")
    except sqlite3.Error as e:
        print(f"Error creating database/table: {e}")
    finally:
        if conn:
            conn.close()


def update_process_status(user_id, updates, db_path=DB_PATH):
    """
    Updates the status fields for a given user_id in the database.
    If the user_id does not exist, a new record is created.

    Args:
        user_id (str): The unique identifier for the user.
        updates (dict): A dictionary where keys are field names (e.g., 'status_step1', 'completion_date')
                        and values are their new status.
        db_path (str): Path to the SQLite database file.
    """

    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        current_time = datetime.datetime.now().isoformat()

       
        cursor.execute(f"PRAGMA table_info({PROCESS_TABLE_NAME});")
        table_columns_info = cursor.fetchall()
        # Extract column names (second element in each tuple)
        existing_columns = {col[1] for col in table_columns_info}

        # Check if the user_id already exists
        cursor.execute(f"SELECT user_id FROM {PROCESS_TABLE_NAME} WHERE user_id = ?", (user_id,))
        existing_user = cursor.fetchone()

        if existing_user:
            # Update existing record
            set_clauses = []
            values = []
            
            # Filter updates to only include fields that exist in the table
            for field, value in updates.items():
                if field in existing_columns and field not in ['user_id', 'last_updated']:
                    set_clauses.append(f"{field} = ?")
                    values.append(value)
            
            # Always update last_updated
            set_clauses.append("last_updated = ?")
            values.append(current_time)
            values.append(user_id) # For the WHERE clause

            if not set_clauses: # If no valid fields were provided in updates
                print(f"No valid fields to update for user '{user_id}'.")
                return

            update_sql = f"UPDATE {PROCESS_TABLE_NAME} SET {', '.join(set_clauses)} WHERE user_id = ?"
            cursor.execute(update_sql, tuple(values))
            #print(f"Updated status for user '{user_id}'.")
        else:
        
            new_record_data = {
                'user_id': user_id,
                'last_updated': current_time
            }

            # Add provided updates, ensuring they are valid columns
            for field, value in updates.items():
                if field in existing_columns and field not in ['user_id', 'last_updated']:
                    new_record_data[field] = value
            
          
            for col_name in existing_columns:
                if col_name not in new_record_data and col_name not in ['user_id', 'last_updated']:
                    new_record_data[col_name] = None 
                    
            columns = ', '.join(new_record_data.keys())
            placeholders = ', '.join(['?' for _ in new_record_data.keys()])
            values = tuple(new_record_data.values())

            insert_sql = f"INSERT INTO {PROCESS_TABLE_NAME} ({columns}) VALUES ({placeholders})"
            cursor.execute(insert_sql, values)
            print(f"Created new status record for user '{user_id}'.")

        conn.commit()
    except sqlite3.Error as e:
        print(f"Error updating process status for user '{user_id}': {e}")
    finally:
        if conn:
            conn.close()
    #print('DEBUG: update DB')

def get_process_status(user_id, field_name=None, db_path=DB_PATH):
    """
    Retrieves the current process status for a given user_id.
    Can optionally retrieve a specific field's status.

    Args:
        user_id (str): The unique identifier for the user.
        field_name (str, optional): The name of the specific field to retrieve
                                    (e.g., 'field1', 'last_updated').
                                    If None, all fields are retrieved.
        db_path (str): Path to the SQLite database file.

    Returns:
        dict or str or None:
            - If field_name is specified, returns the value of that field (str) or None.
            - If field_name is None, returns a dictionary containing all process status fields,
              or None if the user_id is not found.
    """
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        if field_name:
            # Validate field_name to prevent SQL injection
            valid_fields = [f'field{i}' for i in range(1, 9)] + ['user_id', 'last_updated']
            if field_name not in valid_fields:
                print(f"Invalid field name '{field_name}'.")
                return None
            select_sql = f"SELECT {field_name} FROM {PROCESS_TABLE_NAME} WHERE user_id = ?"
            cursor.execute(select_sql, (user_id,))
            row = cursor.fetchone()
            return row[0] if row else None
        else:
            select_sql = f"SELECT * FROM {PROCESS_TABLE_NAME} WHERE user_id = ?"
            cursor.execute(select_sql, (user_id,))
            row = cursor.fetchone()

            if row:
                # Get column names from cursor description
                col_names = [description[0] for description in cursor.description]
                return dict(zip(col_names, row))
            else:
                print(f"No status found for user '{user_id}'.")
                return None
    except sqlite3.Error as e:
        print(f"Error retrieving process status for user '{user_id}': {e}")
        return None
    finally:
        if conn:
            conn.close()

def delete_process_status(user_id, db_path=DB_PATH):
    """
    Deletes the process status entry for a given user_id from the database.

    Args:
        user_id (str): The unique identifier for the user whose entry is to be deleted.
        db_path (str): Path to the SQLite database file.

    Returns:
        bool: True if the entry was deleted (or didn't exist), False if an error occurred.
    """
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        delete_sql = f"DELETE FROM {PROCESS_TABLE_NAME} WHERE user_id = ?"
        cursor.execute(delete_sql, (user_id,))
        conn.commit()

        if cursor.rowcount > 0:
            print(f"Deleted status for user '{user_id}'.")
            return True
        else:
            #print(f"No status found for user '{user_id}' to delete.")
            return True # Still return True as the desired state (absence of user) is met
    except sqlite3.Error as e:
        print(f"Error deleting process status for user '{user_id}': {e}")
        return False
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    create_db_and_table()



