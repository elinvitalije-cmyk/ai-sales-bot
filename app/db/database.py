import sqlite3
from pathlib import Path


DB_FILE = Path("data/leads.db")


def init_db():
    connection = sqlite3.connect(DB_FILE)

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            tariff TEXT NOT NULL,
            call_time TEXT,
            comment TEXT,
            status TEXT NOT NULL DEFAULT 'new',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    columns = cursor.execute(
        """
        PRAGMA table_info(leads)
        """
    ).fetchall()

    column_names = [
        column[1]
        for column in columns
    ]

    if "status" not in column_names:
        cursor.execute(
            """
            ALTER TABLE leads
            ADD COLUMN status TEXT NOT NULL DEFAULT 'new'
            """
        )

    connection.commit()
    connection.close()


def save_lead(lead):
    connection = sqlite3.connect(DB_FILE)

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO leads (
            full_name,
            phone,
            address,
            tariff,
            call_time,
            comment
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            lead["full_name"],
            lead["phone"],
            lead["address"],
            lead["tariff"],
            lead["call_time"],
            lead["comment"],
        ),
    )

    connection.commit()
    connection.close()


def get_all_leads():
    connection = sqlite3.connect(DB_FILE)

    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            full_name,
            phone,
            address,
            tariff,
            call_time,
            comment,
            status,
            created_at
        FROM leads
        ORDER BY id DESC
        """
    )

    rows = cursor.fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]


def get_leads_by_status(status):
    connection = sqlite3.connect(DB_FILE)

    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            full_name,
            phone,
            address,
            tariff,
            call_time,
            comment,
            status,
            created_at
        FROM leads
        WHERE status = ?
        ORDER BY id DESC
        """,
        (status,),
    )

    rows = cursor.fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]


def get_lead_by_id(lead_id):
    connection = sqlite3.connect(DB_FILE)

    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            full_name,
            phone,
            address,
            tariff,
            call_time,
            comment,
            status,
            created_at
        FROM leads
        WHERE id = ?
        """,
        (lead_id,),
    )

    row = cursor.fetchone()

    connection.close()

    if row is None:
        return None

    return dict(row)


def update_lead_status(lead_id, new_status):
    allowed_statuses = {
        "new",
        "called",
        "done",
        "refused",
    }

    if new_status not in allowed_statuses:
        return False

    connection = sqlite3.connect(DB_FILE)

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE leads
        SET status = ?
        WHERE id = ?
        """,
        (
            new_status,
            lead_id,
        ),
    )

    connection.commit()

    was_updated = cursor.rowcount > 0

    connection.close()

    return was_updated
