import sqlite3


class Datastore:
    def __init__(self):
        self.dbFile = "session.db"
        self.c = None
        self.connect()
        self.create()

    def create(self):
        # Create sessions
        self.c.execute(
            """
           CREATE TABLE IF NOT EXISTS session (
               map_n INTEGER,
               tlevel INTEGER,
               reward FLOAT,
               state BLOB
           )
        """
        )

    def connect(self):
        self.conn = sqlite3.connect(self.dbFile)
        self.c = self.conn.cursor()

    def get_mapn(self):
        self.c.execute("SELECT map_n FROM session ORDER BY RANDOM() LIMIT 1")
        return self.c.fetchone()

    def get_count(self):
        self.c.execute("SELECT COUNT(*) FROM session")
        count = self.c.fetchone()
        try:
            return count[0]
        except IndexError:
            return 0

    def get_random(self, map_n: int = 0):
        self.c.execute(
            "SELECT state FROM session WHERE map_n = ? ORDER BY RANDOM() LIMIT 1",
            (map_n,),
        )

        data = self.c.fetchone()
        if data != None:
            try:
                return True, data[0]
            except:
                return False, None
        return False, None

    def write_session(self, map_n: int, tlevel: int, reward: float, state: bytes):
        # Insert data into session table
        self.c.execute(
            """
         INSERT INTO session (map_n, tlevel, reward, state)
         VALUES (?, ?, ?, ?)
        """,
            (map_n, tlevel, reward, state),
        )

        # Commit the transaction
        self.conn.commit()
