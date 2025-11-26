import sqlite3

try:
    conn = sqlite3.connect('cj36.db')
    cursor = conn.cursor()
    
    with open('db_status.txt', 'w') as f:
        # Check users
        try:
            cursor.execute("SELECT id, username FROM user")
            users = cursor.fetchall()
            f.write(f"Total users: {len(users)}\n")
            for user in users:
                f.write(f"User: {user[1]}\n")
        except Exception as e:
            f.write(f"Error checking users: {e}\n")

        # Check categories
        try:
            cursor.execute("SELECT id, name FROM category")
            categories = cursor.fetchall()
            f.write(f"Total categories: {len(categories)}\n")
            for cat in categories:
                f.write(f"Category: {cat[1]}\n")
        except Exception as e:
            f.write(f"Error checking categories: {e}\n")

        # Check posts
        try:
            cursor.execute("SELECT id, title FROM post")
            posts = cursor.fetchall()
            f.write(f"Total posts: {len(posts)}\n")
        except Exception as e:
             f.write(f"Error checking posts: {e}\n")

    conn.close()
except Exception as e:
    with open('db_status.txt', 'w') as f:
        f.write(f"Error connecting: {e}\n")
