from databases import Database

database = Database("sqlite:///./test.db")

async def create_tables():
    await database.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )
    """)

create_tables()