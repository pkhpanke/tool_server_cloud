import mysql.connector
from mysql.connector import Error, pooling
import threading
from datetime import datetime, timedelta

class DatabaseHandler:
    _pool = None

    @classmethod
    def initialize_pool(cls, **db_config):
        cls._pool = mysql.connector.pooling.MySQLConnectionPool(
            pool_name="mypool",
            pool_size=5, # Adjust pool size as needed
            **db_config
        )

    def __init__(self):
        self.conn = None
        self.lock = threading.Lock()

    def connect(self):
        if not DatabaseHandler._pool:
            raise Exception("Database pool not initialized")
        self.conn = DatabaseHandler._pool.get_connection()

    def is_user_access_valid(self, access_key):
        with self.lock:
            try:
                cursor = self.conn.cursor()
                query = """
                SELECT id, user_name, current_usage, max_usage FROM user_information 
                WHERE access_key = %s
                """
                cursor.execute(query, (access_key,))
                row = cursor.fetchone()

                if row:
                    user_id, user_name, current_usage, max_usage = row
                    if max_usage == -1:
                        return None
                    elif max_usage == 0 or current_usage < max_usage:
                        return user_id, user_name
                return None
            except Error as e:
                print(e)
                return None
            finally:
                cursor.close()
    def insert_visit_log_login(self,user_id, user_name, session_id):
        with self.lock:
            try:
                cursor = self.conn.cursor()
                # SQL query to insert a new row
                query = """
                INSERT INTO visit_log (user_id, user_name, session_id) 
                VALUES (%s, %s, %s)
                """
                # Execute the query
                cursor.execute(query, (user_id, user_name, session_id))
                self.conn.commit()
                print("New visit log entry inserted.")
            except Error as e:
                print(e)
            finally:
                cursor.close()

    def get_field_value_for_key(self, table, key_field, key_value, field_to_retrieve):
        with self.lock:
            try:
                cursor = self.conn.cursor()
                # SQL query to get the specified field for a given key
                query = f"SELECT {field_to_retrieve} FROM {table} WHERE {key_field} = %s"
                # Execute the query
                cursor.execute(query, (key_value,))
                result = cursor.fetchone()

                if result:
                    return result[0]  # Return the value of the specified field
                else:
                    return None  # Item not found or key does not exist
            except Error as e:
                print("Error while connecting to MySQL", e)
                return None
            finally:
                cursor.close()

    def check_value_correctness(self, table, key_field, key_value):
        with self.lock:
            try:
                cursor = self.conn.cursor()
                # SQL query to check the value
                query = f"SELECT EXISTS(SELECT 1 FROM {table} WHERE {key_field} = %s)"
                # Execute the query
                cursor.execute(query, (key_value,))
                result = cursor.fetchone()

                return result[0] == 1
            except Error as e:
                print("Error while connecting to MySQL", e)
                return False
            finally:
                cursor.close()
    
    def check_sessionid(self, session_id):
        if not self.check_value_correctness('visit_log','session_id',session_id):
            return False
        
        # Get the creation time of the session
        creation_time = self.get_field_value_for_key('visit_log', 'session_id', session_id, 'visit_time')
        if creation_time is None:
            return False

        # Convert creation_time to a datetime object if it's not already
        if not isinstance(creation_time, datetime):
            creation_time = datetime.strptime(creation_time, "%Y-%m-%d %H:%M:%S")
         # Check if the current time is more than 5 minutes from the creation time
        current_time = datetime.now()
        if current_time - creation_time > timedelta(minutes=5):
            return False

        return True
    
    def get_analysis_result_fromdatabase(self, session_id):
        return self.get_field_value_for_key('visit_log', 'session_id', session_id, 'analysis_result')

    def insert_visit_log(self, log_data):
        with self.lock:
            try:
                cursor = self.conn.cursor()
                query = """
                INSERT INTO visit_log (user_id, user_name, product_link, analysis_success, analysis_result, error_code, model, finish_reason, token_input, token_output) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                data = (log_data['user_id'], log_data['user_name'], log_data['product_link'], log_data['analysis_success'], 
                        log_data['analysis_result'], log_data['error_code'], log_data['model'], log_data['finish_reason'], log_data['token_input'], log_data['token_output'])
                cursor.execute(query, data)
                self.conn.commit()
                print("New visit log entry inserted.")
            except Error as e:
                print(e)
            finally:
                cursor.close()

    def update_visit_log(self, session_id, data, user_id = None):
        with self.lock:
            try:
                cursor = self.conn.cursor()
                # Determine which identifier and column to use
                identifier, identifier_column = (user_id, "user_id") if user_id is not None else (session_id, "session_id")
                if identifier is None:
                    raise ValueError("Either user_id or user_key must be provided")
                # Preparing the SET part of the SQL update query
                set_clause = ', '.join([f"{key} = %s" for key in data.keys()])
                values = list(data.values())

                # SQL query to update an existing row
                query = f"UPDATE visit_log SET {set_clause} WHERE {identifier_column} = %s"

                # Execute the query
                cursor.execute(query, values + [identifier])
                self.conn.commit()

                if cursor.rowcount == 0:
                    print("No rows were updated. Please check the session_id.")
                else:
                    print("Visit log entry updated successfully.")

            except Error as e:
                print("Error while connecting to MySQL", e)
            finally:
                cursor.close()

    def update_user_usage(self, user_id, token_usage_increment, user_key=None):
        with self.lock:
            try:
                cursor = self.conn.cursor(buffered=True)
                # Determine which identifier and column to use
                identifier, identifier_column = (user_id, "id") if user_id is not None else (user_key, "access_key")
                if identifier is None:
                    raise ValueError("Either user_id or user_key must be provided")
                
                # Fetch the current values
                select_query = f"""
                SELECT current_usage, current_token_usage FROM user_information 
                WHERE {identifier_column} = %s
                """
                cursor.execute(select_query, (identifier,))
                row = cursor.fetchone()

                if row:
                    current_usage, current_token_usage = row
                    new_current_usage = current_usage + 1
                    new_current_token_usage = current_token_usage + token_usage_increment

                    # Update with incremented values
                    update_query = f"""
                    UPDATE user_information 
                    SET current_usage = %s, current_token_usage = %s 
                    WHERE {identifier_column} = %s
                    """
                    cursor.execute(update_query, (new_current_usage, new_current_token_usage, identifier))
                    self.conn.commit()
                    print(f"User with {identifier_column} '{identifier}' usage incremented.")
                else:
                    print(f"No user found with ID with {identifier_column} '{identifier}'")

            except Error as e:
                print(e)
            finally:
                cursor.close()

    def close(self):
        if self.conn.is_connected():
            self.conn.close()

# Example usage
if __name__ == '__main__':
    DatabaseHandler.initialize_pool(host="localhost", database="pso_voc_tool", user="root", password="")
    db = DatabaseHandler()
    db.connect()

    # Checking user access
    user_details = db.is_user_access_valid("sk-Q6qyMsryBQ5LDrIvFV3DgIJ6a718LI8NGM5iUKyXanLy0mCV")
    if user_details:
        print(f"User ID: {user_details[0]}, User Name: {user_details[1]}")
    else:
        print("Access not valid or user does not exist.")

    # Inserting a visit log
    log_data = {
        'user_id': user_details[0],  # Example values
        'user_name': user_details[1],
        'product_link': 'http://example.com/product',
        'analysis_success': 1,
        'analysis_result': 'Testing',
        'error_code': 'None',
        'token_input': 0,
        'token_output': 0
    }
    db.insert_visit_log(log_data)
    db.update_user_usage(user_id=user_details[0], token_usage_increment=0)

    db.close()
