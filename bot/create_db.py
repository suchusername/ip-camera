import sqlite3
from sqlite3 import Error


def create_connection(db_file):
    """ create a database connection to a SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(sqlite3.version)
    except Error as e:
        print(e)
    finally:
        if conn:
            conn.close()
            

def create(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        
        c.execute("""DROP TABLE IF EXISTS users""")
        c.execute("""CREATE TABLE "users" (
                            "user_id"    INTEGER PRIMARY KEY ,
                            "user_name"  TEXT,
                            "stream_url" TEXT,
                            "isRunning"  INTEGER
                     );""")

        conn.commit()
    except Error as e:
        print(e)
    finally:
        if conn:
            conn.close()
            
            
            
            



if __name__ == '__main__':
    db_path = r"data_users.db"
#     create_connection(db_path)
#     create(db_path)   
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    sql = "SELECT * FROM users "
    recs = c.execute(sql).fetchall()
    print(recs)
    c.close()
    