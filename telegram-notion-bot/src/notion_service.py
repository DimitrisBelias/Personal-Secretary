"""
Notion Service - handles all interactions with Notion API
"""
from notion_client import Client
from datetime import datetime, timedelta
import config

# Initialize Notion client
notion = Client(auth=config.NOTION_TOKEN)


def add_assignment(title, course, due_date, notes="", status="Not started"):
    """
    Add a new assignment to the Assignments database
    
    Args:
        title: Assignment title (e.g., "Homework 3")
        course: Course code (e.g., "PHY202")
        due_date: Due date as string "YYYY-MM-DD" (e.g., "2024-11-25")
        notes: Optional notes about the assignment
        status: Status - "Not started", "In progress", or "Done"
    
    Returns:
        True if successful, False otherwise
    """
    try:
        new_page = notion.pages.create(
            parent={"database_id": config.ASSIGNMENTS_DB_ID},
            properties={
                "Title": {
                    "title": [
                        {
                            "text": {
                                "content": title
                            }
                        }
                    ]
                },
                "Due Date": {
                    "date": {
                        "start": due_date
                    }
                },
                "Course Code": {  # Changed from "Course"
                    "rich_text": [
                        {
                            "text": {
                                "content": course
                            }
                        }
                    ]
                },
                "Notes": {
                    "rich_text": [
                        {
                            "text": {
                                "content": notes
                            }
                        }
                    ]
                },
                "status": {  # New status field!
                    "status": {
                        "name": status
                    }
                }
            }
        )
        return True
    except Exception as e:
        print(f"Error adding assignment: {e}")
        return False


def query_upcoming_assignments(days=7):
    """
    Query assignments due in the next X days
    
    Args:
        days: Number of days to look ahead (default: 7)
    
    Returns:
        List of assignment dictionaries with title, course, and due_date
    """
    try:
        # Calculate date range
        today = datetime.now().date().isoformat()
        future_date = (datetime.now().date() + timedelta(days=days)).isoformat()
        
        # Query the database
        response = notion.databases.query(
            database_id=config.ASSIGNMENTS_DB_ID,
            filter={
                "and": [
                    {
                        "property": "Due Date",
                        "date": {
                            "on_or_after": today
                        }
                    },
                    {
                        "property": "Due Date",
                        "date": {
                            "on_or_before": future_date
                        }
                    }
                ]
            },
            sorts=[
                {
                    "property": "Due Date",
                    "direction": "ascending"
                }
            ]
        )
        
        # Parse results
        assignments = []
        for page in response["results"]:
            props = page["properties"]
            
            # Extract title
            title = props["Title"]["title"][0]["text"]["content"] if props["Title"]["title"] else "Untitled"
            
            # Extract course
            course = props["Course Code"]["rich_text"][0]["text"]["content"] if props["Course"]["rich_text"] else "N/A"
            
            # Extract due date
            due_date = props["Due Date"]["date"]["start"] if props["Due Date"]["date"] else "No date"
            
            assignments.append({
                "title": title,
                "course": course,
                "due_date": due_date
            })
        
        return assignments
    
    except Exception as e:
        print(f"Error querying assignments: {e}")
        return []



def test_notion_connection():
    """Test if we can connect to Notion API"""
    try:
        # Try to retrieve the assignments database
        response = notion.databases.retrieve(database_id=config.ASSIGNMENTS_DB_ID)
        print(f"✅ Connected to Notion! Database: {response['title'][0]['plain_text']}")
        return True
    except Exception as e:
        print(f"❌ Failed to connect to Notion: {e}")
        return False



def inspect_database_schema(database_id):
    """Print out the structure of a Notion database"""
    try:
        response = notion.databases.retrieve(database_id=database_id)
        print("\n📊 Database Properties:\n")
        
        for prop_name, prop_data in response["properties"].items():
            print(f"Property: {prop_name}")
            print(f"  Type: {prop_data['type']}")
            print(f"  Full data: {prop_data}\n")
        
        return response["properties"]
    except Exception as e:
        print(f"Error: {e}")
        return None
    
    

# Test function to verify everything works
if __name__ == "__main__":
    print("Testing Notion connection...")
    test_notion_connection()
    
    inspect_database_schema(config.ASSIGNMENTS_DB_ID)
    
    print("\nTesting query assignments...")
    assignments = query_upcoming_assignments(30)
    print(f"Found {len(assignments)} upcoming assignments:")
    for assignment in assignments:
        print(f"  - {assignment['title']} ({assignment['course']}) - Due: {assignment['due_date']}")
        
    