import sqlite3

def check_recent_tasks():
    conn = sqlite3.connect('orc.db')
    cur = conn.cursor()
    
    cur.execute("SELECT id, description, status FROM task ORDER BY created_at DESC LIMIT 5")
    tasks = cur.fetchall()
    
    for task in tasks:
        task_id, description, status = task
        print(f"\n--- Task: {description} | Status: {status} | ID: {task_id} ---")
        
        cur.execute("SELECT interaction_type, content, timestamp FROM memory WHERE task_id = ? ORDER BY timestamp ASC", (task_id,))
        memories = cur.fetchall()
        for m in memories:
            print(f"  [{m[2]}] {m[0]}: {m[1]}")
            
    conn.close()

if __name__ == "__main__":
    check_recent_tasks()
