from cj36.core.config import settings
with open("config_output.txt", "w") as f:
    f.write(f"DB URL: {settings.db_url}\n")
