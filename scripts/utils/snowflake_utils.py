import logging
import snowflake.connector
from dotenv import load_dotenv
import os

load_dotenv()


def snowflake_connection():
    """
    Create a connection to Snowflake
    """

    config = {
            "user": os.getenv("USERNAME"),
            "account": os.getenv("SNOWFLAKE_ACCOUNT"),
            "role": os.getenv("ROLE"),
            "warehouse": os.getenv("WAREHOUSE"),
            "password": os.getenv("PASSWORD"),
        }
    return snowflake.connector.connect(**config)



def execute_query(
    query, returns_results: bool = False, log: str = "Query successfully executed"
):
    """
    Executes the given query/queries. If query is a str, the query will be executed and can return results.
    If the query is a list of strings, all the queries will be executed in one session and cannot return results.
    Returns a list of dictionaries if returns_results = True
    """
    try:
        with snowflake_connection() as con:
            if isinstance(query, str):
                cursor = con.cursor()
                results = cursor.execute(query)
                if returns_results:
                    rows = results.fetchall()
                    # Get column names from the cursor description
                    column_names = [desc[0] for desc in results.description]
                    # Create a list of dictionaries
                    result_list = [dict(zip(column_names, row)) for row in rows]

                    return result_list

            elif isinstance(query, list):
                cursor = con.cursor()
                for idx, qry in enumerate(query):
                    cursor.execute(qry)
                    logging.info(f"executed query {idx+1}/{len(query)} successfully")
            else:
                raise ValueError("query is neither a string or a list of strings")

            logging.info(log)

    except snowflake.connector.errors.ProgrammingError as e:
        error = f"An error occurred while executing the query: {e}"
        raise Exception(error)
