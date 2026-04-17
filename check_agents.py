import sqlite3

def check_agents():
    conn = sqlite3.connect('orc.db')
    cur = conn.cursor()
    cur.execute("SELECT id, name, specializations, tools, model_name FROM agent")
    rows = cur.fetchall()
    for row in rows:
        print(f"Agent: {row[1]}")
        print(f"  Specializations: {row[2]} (type: {type(row[2])})")
        print(f"  Tools: {row[3]} (type: {type(row[3])})")
        print(f"  Model: {row[4]}")
    conn.close()

if __name__ == "__main__":
    check_agents()
