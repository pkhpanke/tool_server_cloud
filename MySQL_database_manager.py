import mysql.connector
from mysql.connector import Error, pooling
import threading

class MySQLDatabaseManager:
    _pool = None
    _pool_lock = threading.Lock()

    @classmethod
    def initialize_pool(cls, **db_config):
        with cls._pool_lock:
            if cls._pool is None:
                cls._pool = mysql.connector.pooling.MySQLConnectionPool(
                    pool_name="mypool",
                    pool_size=5,  # Adjust pool size as needed
                    **db_config
                )

    def __init__(self):
        self.conn = None
        self.lock = threading.Lock()


        """
        Establish a connection to the database using a connection from the pool.
        This method ensures that each instance of this class has its own unique connection.
        Raises an exception if the connection pool is not initialized.
        """
    def connect(self):
        with self.lock:
            if not self.conn:
                if not MySQLDatabaseManager._pool:
                    raise Exception("Database pool not initialized")
                self.conn = MySQLDatabaseManager._pool.get_connection()

    # Include all methods that interact directly with the database
    # ...

    def close(self):
        with self.lock:
            if self.conn and self.conn.is_connected():
                self.conn.close()
                self.conn = None


    """
        Retrieve a specific field value from a row in the database.

        :param table: The name of the database table to query.
        :param key_field: The column name to use as the key for the query.
        :param key_value: The value of the key field to look for.
        :param field_to_retrieve: The name of the column whose value needs to be retrieved.
        :return: The value of the specified field if the row is found, None otherwise.
    """
    def get_value_for_key(self, table, key_field, key_value, field_to_retrieve):
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

        """
        Retrieve multiple field values from a row in the database.

        :param table: The name of the database table to query.
        :param key_field: The column name to use as the key for the query.
        :param key_value: The value of the key field to look for.
        :param fields_to_retrieve: A list of column names whose values need to be retrieved.
        :return: A dictionary mapping each field name to its value if the row is found, None otherwise.
        """
    def get_value_for_keys(self, table, key_field, key_value, fields_to_retrieve):
        with self.lock:
            try:
                cursor = self.conn.cursor()

                # Joining the fields to retrieve into a single string for the SQL query
                fields = ', '.join(fields_to_retrieve)

                # SQL query to get the specified fields for a given key
                query = f"SELECT {fields} FROM {table} WHERE {key_field} = %s"
                
                # Execute the query
                cursor.execute(query, (key_value,))
                result = cursor.fetchone()

                if result:
                    # Mapping the field names to their corresponding values in the result
                    return dict(zip(fields_to_retrieve, result))
                else:
                    return None  # Item not found or key does not exist

            except Error as e:
                print("Error while connecting to MySQL", e)
                return None
            finally:
                cursor.close()


        """
        Update a specific field in a row in the database.

        :param table: The name of the database table to update.
        :param key_field: The column name to use as the key for the update operation.
        :param key_value: The value of the key field for the row to be updated.
        :param field_to_update: The name of the column to be updated.
        :param new_value: The new value to be set for the field.
        :return: True if the update was successful, False otherwise.
        """
    def update_value_for_key(self, table, key_field, key_value, field_to_update, new_value):
        with self.lock:
            try:
                cursor = self.conn.cursor()
                # SQL query to update the specified field for a given key
                query = f"UPDATE {table} SET {field_to_update} = %s WHERE {key_field} = %s"
                # Execute the query
                cursor.execute(query, (new_value, key_value))
                self.conn.commit()

                if cursor.rowcount > 0:
                    print(f"Field '{field_to_update}' updated successfully in {table}.")
                    return True
                else:
                    print(f"No rows were updated in {table}. Please check the {key_field}.")
                    return False
            except Error as e:
                print("Error while connecting to MySQL", e)
                return False
            finally:
                cursor.close()


        """
        Update multiple fields in a row in the database.

        :param table: The name of the database table to update.
        :param key_field: The column name to use as the key for the update operation.
        :param key_value: The value of the key field for the row to be updated.
        :param data: A dictionary where keys are the column names to be updated and values are the new values.
        :return: True if the update was successful, False otherwise.
        """
    def update_value_for_keys(self, table, key_field, key_value, data):
        with self.lock:
            try:
                cursor = self.conn.cursor()
                # Preparing the SET part of the SQL update query
                set_clause = ', '.join([f"{key} = %s" for key in data.keys()])
                values = list(data.values())

                # SQL query to update an existing row
                query = f"UPDATE {table} SET {set_clause} WHERE {key_field} = %s"

                # Execute the query
                cursor.execute(query, values + [key_value])
                self.conn.commit()

                if cursor.rowcount == 0:
                    print("No rows were updated. Please check the session_id.")
                else:
                    print("Visit log entry updated successfully.")

            except Error as e:
                print("Error while connecting to MySQL", e)
            finally:
                cursor.close()
    
        """
        Insert a new row into a database table.

        :param table: The name of the database table where the new row will be inserted.
        :param data: A dictionary containing the data to be inserted. Keys are column names and values are the data for those columns.
        :return: The ID of the newly inserted row if successful, None otherwise.
        """
    def insert_row(self, table, data):
        with self.lock:
            try:
                cursor = self.conn.cursor()

                # Preparing the column names and placeholder for values
                columns = ', '.join(data.keys())
                placeholders = ', '.join(['%s'] * len(data))

                # SQL query to insert a new row
                query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

                # Execute the query
                cursor.execute(query, list(data.values()))
                self.conn.commit()

                if cursor.lastrowid:
                    print(f"New row inserted successfully in {table}, ID: {cursor.lastrowid}")
                    return cursor.lastrowid
                else:
                    print("No row was inserted.")
                    return None

            except Error as e:
                print("Error while connecting to MySQL", e)
                return None
            finally:
                cursor.close()

        """
        Retrieve an entire row from a database table based on a given key.

        :param table: The name of the database table to query.
        :param key_field: The column name to use as the key for the query.
        :param key_value: The value of the key field to look for.
        :return: A dictionary representing the row if found, None otherwise.
        """
    def get_row(self, table, key_field, key_value):
        with self.lock:
            try:
                cursor = self.conn.cursor(dictionary=True)

                # SQL query to get the entire row for a given key
                query = f"SELECT * FROM {table} WHERE {key_field} = %s"
                
                # Execute the query
                cursor.execute(query, (key_value,))
                result = cursor.fetchone()

                return result  # Returns the entire row as a dictionary or None if not found

            except Error as e:
                print("Error while connecting to MySQL", e)
                return None
            finally:
                cursor.close()

    
        """
        Delete a row from a database table based on a given key.

        :param table: The name of the database table from which to delete the row.
        :param key_field: The column name to use as the key for the delete operation.
        :param key_value: The value of the key field for the row to be deleted.
        :return: True if the row was successfully deleted, False otherwise.
        """
    def delete_row(self, table, key_field, key_value):
        with self.lock:
            try:
                cursor = self.conn.cursor()

                # SQL query to delete a row based on the key field
                query = f"DELETE FROM {table} WHERE {key_field} = %s"

                # Execute the query
                cursor.execute(query, (key_value,))
                self.conn.commit()

                if cursor.rowcount > 0:
                    print(f"Row deleted successfully from {table}.")
                    return True
                else:
                    print(f"No row was deleted. Please check the {key_field}.")
                    return False

            except Error as e:
                print("Error while connecting to MySQL", e)
                return False
            finally:
                cursor.close()


