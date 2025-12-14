"""
Configuration file - loads environment variables and provides them to the app
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Notion API Configuration
NOTION_TOKEN = os.getenv("NOTION_TOKEN")


# Notion Database IDs
ASSIGNMENTS_DB_ID = os.getenv("ASSIGNMENTS_DB_ID")
LABS_DB_ID = os.getenv("LABS_DB_ID")
PROJECTS_DB_ID = os.getenv("PROJECTS_DB_ID")
COURSES_DB_ID = os.getenv("COURSES_DB_ID")

# Validate that all required environment variables are set
def validate_config():
    """Check if all required environment variables are set"""
    required_vars = {
        "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
        "NOTION_TOKEN": NOTION_TOKEN,
        "ASSIGNMENTS_DB_ID": ASSIGNMENTS_DB_ID,
        "LABS_DB_ID": LABS_DB_ID,
        "PROJECTS_DB_ID": PROJECTS_DB_ID,
        "COURSES_DB_ID": COURSES_DB_ID,
    }
    
    missing_vars = [var_name for var_name, var_value in required_vars.items() if not var_value]
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    print("✅ All configuration variables loaded successfully!")
    return True