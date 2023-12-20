import sqlite3


class Datastore:
    def __init__(self):
        self.dbFile = "session.db"
        self.c = None
        self.connect()
        self.create()

    def create(self):
        # Create map
        self.c.execute("CREATE TABLE IF NOT EXISTS map (map_n INTEGER UNIQUE)")
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

    def get_count(self):
        self.c.execute("SELECT COUNT(*) FROM session")
        count = self.c.fetchone()
        try:
            return count[0]
        except IndexError:
            return 0

    def get_random(self):
        self.c.execute(
            """
            SELECT state FROM session WHERE map_n = (
                SELECT map_n FROM map ORDER BY RANDOM() LIMIT 1
            )
            ORDER BY tlevel LIMIT 1
            """
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

    def migrate_mapn(self):
        # move map_n from session to map
        self.c.execute(
            """
                INSERT OR IGNORE INTO map(map_n)
                SELECT DISTINCT map_n FROM session
            """
        )
