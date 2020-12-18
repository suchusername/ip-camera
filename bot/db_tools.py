from sqlite3 import Error
import sqlite3 as lite

DB_PATH = "/ip-camera/bot/db/data_users.db"


def create_connection(db_file):
    """ create a database connection to a SQLite database """
    conn = None
    try:
        conn = lite.connect(db_file)
    except Error as e:
        print(e)
    finally:
        if conn:
            conn.close()


def create(db_file):
    conn = None
    try:
        conn = lite.connect(db_file)
        c = conn.cursor()

        c.execute("""DROP TABLE IF EXISTS users""")
        c.execute(
            """CREATE TABLE "users" (
                            "user_id"    INTEGER PRIMARY KEY ,
                            "user_name"  TEXT,
                            "isRunning"  INTEGER,
                            "msg_id"     INTEGER,
                            "camera_ip"  TEXT,
                            "pan"        REAL,
                            "tilt"       REAL,
                            "zoom"       REAL
                     );"""
        )

        conn.commit()
    except Error as e:
        print(e)
    finally:
        if conn:
            conn.close()


def new_users(user_id, username, isRunning, msg_id, data_users=DB_PATH):
    con = lite.connect(data_users)
    cur = con.cursor()
    cur.execute("select user_id from users WHERE user_id = ?", (user_id,))

    if not (user_id,) in cur.fetchall():
        con = lite.connect(data_users)
        cur = con.cursor()
        cur.execute(
            "INSERT INTO users VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, username, isRunning, msg_id, "NULL", "NULL", "NULL", "NULL"),
        )

        con.commit()
    cur.close()


def update_by_id(user_id, column_name, value, table="users", data_users=DB_PATH):
    con = lite.connect(data_users)
    cur = con.cursor()
    cur.execute(
        f"UPDATE {table} SET {column_name}=? WHERE user_id=?", (value, user_id,)
    )
    con.commit()
    cur.close()


def select_by_id(user_id, column_name, table="users", data_users=DB_PATH):

    con = lite.connect(data_users)
    cur = con.cursor()
    recs = cur.execute(
        f"SELECT {column_name} FROM {table} WHERE user_id={user_id}"
    ).fetchall()

    cur.close()
    return recs[0][0]


def insert_camera_by_ip(
    user_id, camera_ip, configuration, table="cameras", data_users=DB_PATH
):
    con = lite.connect(data_users)
    cur = con.cursor()
    recs = cur.execute(
        f"select user_id, camera_ip from {table} WHERE user_id = ? AND camera_ip = ?",
        (user_id, camera_ip),
    ).fetchall()

    if not (user_id, camera_ip) in recs:

        cur.execute(
            f"INSERT INTO {table} VALUES(?, ?, ?, ?, ?)",
            (
                user_id,
                camera_ip,
                configuration["pan"],
                configuration["tilt"],
                configuration["zoom"],
            ),
        )
        con.commit()

    cur.close()


def select_conf_by_id(user_id, table="users", data_users=DB_PATH):

    con = lite.connect(data_users)
    cur = con.cursor()

    recs = cur.execute(
        f"SELECT pan, tilt, zoom FROM {table} WHERE user_id={user_id}"
    ).fetchall()

    cur.close()
    return recs[0]


def update_camera_by_id(user_id, camera_ip, column_name, value, data_users=DB_PATH):
    con = lite.connect(data_users)
    cur = con.cursor()
    cur.execute(
        f"UPDATE camera SET {column_name}=? WHERE user_id=? AND ",
        (value, user_id, camera_ip),
    )
    con.commit()
    cur.close()


if __name__ == "__main__":
    db_path = repr(DB_PATH)
    #     create_connection(db_path)
    #     create(db_path)

    conn = lite.connect(db_path)
    c = conn.cursor()
    sql = "SELECT * FROM users "
    recs = c.execute(sql).fetchall()
    print(recs)

    c.close()
