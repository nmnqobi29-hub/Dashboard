"""
Imports residence student data from residence_student_test_data.xlsx
into Railway Postgres (residents table).

Run this locally, from the same folder as the .xlsx file and db.py.
Make sure the residents table already exists (run create_residents_table.sql first).

Safe to re-run: it will simply add duplicate rows if run twice, since there's
no unique constraint yet (student_number has a known duplicate pending review).
If you re-run this, consider truncating the table first:
    TRUNCATE TABLE residents RESTART IDENTITY;
"""

import pandas as pd
from db import get_connection

EXCEL_PATH = "residence_student_test_data.xlsx"


def clean_lease_status(value: str) -> str:
    """Fixes the 'Uknown' typo found in the source file."""
    if value.strip().lower() == "uknown":
        return "Unknown"
    return value.strip()


def migrate():
    df = pd.read_excel(EXCEL_PATH)

    if df.empty:
        print("No rows found in the spreadsheet. Nothing to import.")
        return

    print(f"Found {len(df)} row(s) in {EXCEL_PATH}. Importing to Railway Postgres...")

    conn = get_connection()
    cursor = conn.cursor()

    imported = 0

    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO residents
            (student_number, student_name, room_number, academic_year, lease_status)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            int(row["STUDENT_NUMBER"]),
            str(row["STUDENT_NAME"]).strip(),
            str(row["ROOM_NUMBER"]).strip(),
            str(row["ACADEMIC_YEAR"]).strip(),
            clean_lease_status(str(row["LEASE_STATUS"])),
        ))
        imported += 1

    conn.commit()
    conn.close()

    print(f"Done. Imported: {imported} row(s).")


if __name__ == "__main__":
    migrate()
