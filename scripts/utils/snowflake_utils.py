import logging
import snowflake.connector
from dotenv import load_dotenv
import os

load_dotenv()


def snowflake_connection():
    """
    Establishes a connection to Snowflake using credentials from environment variables.
    """

    config = {
        "user": os.getenv("USERNAME"),
        "account": os.getenv("SNOWFLAKE_ACCOUNT"),
        "role": os.getenv("ROLE"),
        "warehouse": os.getenv("WAREHOUSE"),
        "password": os.getenv("PASSWORD"),
    }
    return snowflake.connector.connect(**config)


def execute_query(query: str) -> list[dict]:
    """
    Execute a SQL query against the Snowflake database and return the results as a list of dictionaries.
    """
    try:
        with snowflake_connection() as con:
            cursor = con.cursor()
            results = cursor.execute(query)

            rows = results.fetchall()
            # Get column names from the cursor description
            column_names = [desc[0] for desc in results.description]
            # Create a list of dictionaries with column names as keys
            result_list = [dict(zip(column_names, row)) for row in rows]
            return result_list

    except snowflake.connector.errors.ProgrammingError as e:
        error = f"An error occurred while executing the query: {e}"
        raise Exception(error)
