import sqlite3
from tabulate import tabulate
from datetime import datetime

DB_FILE = "entries.db"

def connect_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    return conn, cursor

def show_entries(filter_date=None, filter_text=None):
    conn, cursor = connect_db()
    query = "SELECT id, date, journal, intention, dream, priorities, reflection, strategy FROM entries WHERE 1=1"
    params = []

    if filter_date:
        query += " AND date = ?"
        params.append(filter_date.strftime("%Y-%m-%d"))
    if filter_text:
        query += " AND (journal LIKE ? OR intention LIKE ?)"
        params.extend([f"%{filter_text}%", f"%{filter_text}%"])

    query += " ORDER BY id DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()

    if not rows:
        print("⚠️ No entries found.")
    else:
        headers = ["ID", "Date", "Journal", "Intention", "Dream", "Priorities", "Reflection", "Strategy"]
        print(tabulate(rows, headers=headers, tablefmt="grid"))

    conn.close()
    return rows

def delete_entry(entry_id):
    conn, cursor = connect_db()
    cursor.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
    conn.commit()
    print(f"✅ Entry {entry_id} deleted successfully!")
    conn.close()

def main():
    while True:
        print("\n--- Conscious Day DB Manager ---")
        print("1. Show all entries")
        print("2. Show latest entry")
        print("3. Search by date")
        print("4. Search by keyword")
        print("5. Delete entry")
        print("6. Exit")

        choice = input("Choose an option: ")

        if choice == "1":
            show_entries()
        elif choice == "2":
            rows = show_entries()
            if rows:
                print("\n--- Latest Entry ---")
                latest = rows[0]
                headers = ["ID", "Date", "Journal", "Intention", "Dream", "Priorities", "Reflection", "Strategy"]
                print(tabulate([latest], headers=headers, tablefmt="grid"))
        elif choice == "3":
            date_input = input("Enter date (YYYY-MM-DD): ")
            try:
                date_obj = datetime.strptime(date_input, "%Y-%m-%d")
                show_entries(filter_date=date_obj)
            except:
                print("❌ Invalid date format.")
        elif choice == "4":
            keyword = input("Enter keyword to search (Journal/Intention): ")
            show_entries(filter_text=keyword)
        elif choice == "5":
            try:
                entry_id = int(input("Enter Entry ID to delete: "))
                delete_entry(entry_id)
            except:
                print("❌ Invalid ID.")
        elif choice == "6":
            print("Exiting...")
            break
        else:
            print("❌ Invalid option. Try again.")

if __name__ == "__main__":
    main()
