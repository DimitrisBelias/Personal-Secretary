"""
Notion Service - handles all interactions with Notion API
"""

from notion_client import Client
from datetime import datetime, timedelta
import config

# Initialize Notion client
notion = Client(auth=config.NOTION_TOKEN)


# =============================================================================
# ASSIGNMENT OPERATIONS
# =============================================================================

def add_assignment(name: str, course_code: str, due_date: str, notes: str = "", status: str = "Not started") -> dict:
    """
    Add a new assignment to the Assignments database.
    
    Args:
        name: Assignment name (e.g., "Homework 3")
        course_code: Course code (e.g., "PHY202")
        due_date: Due date in YYYY-MM-DD format
        notes: Optional notes
        status: "Not started", "In progress", or "Done"
    
    Returns:
        dict with success status and message
    """
    try:
        response = notion.pages.create(
            parent={"database_id": config.ASSIGNMENTS_DB_ID},
            properties={
                "Name": {
                    "title": [{"text": {"content": name}}]
                },
                "Course Code": {
                    "rich_text": [{"text": {"content": course_code}}]
                },
                "Due Date": {
                    "date": {"start": due_date}
                },
                "Notes": {
                    "rich_text": [{"text": {"content": notes}}]
                },
                "status": {
                    "status": {"name": status}
                }
            }
        )
        return {"success": True, "message": f"Assignment '{name}' added successfully!"}
    except Exception as e:
        return {"success": False, "message": f"Error adding assignment: {str(e)}"}


def list_assignments() -> list:
    """Get all assignments sorted by due date."""
    try:
        response = notion.databases.query(
            database_id=config.ASSIGNMENTS_DB_ID,
            sorts=[{"property": "Due Date", "direction": "ascending"}]
        )
        return _parse_items(response["results"], "assignment")
    except Exception as e:
        print(f"Error listing assignments: {e}")
        return []


# =============================================================================
# LAB OPERATIONS
# =============================================================================

def add_lab(name: str, course_code: str, due_date: str, description: str = "", notes: str = "", status: str = "Not started") -> dict:
    """
    Add a new lab to the Labs database.
    
    Args:
        name: Lab name (e.g., "Lab 5")
        course_code: Course code (e.g., "PHY202")
        due_date: Due date in YYYY-MM-DD format
        description: Optional description
        notes: Optional notes
        status: "Not started", "In progress", or "Done"
    
    Returns:
        dict with success status and message
    """
    try:
        response = notion.pages.create(
            parent={"database_id": config.LABS_DB_ID},
            properties={
                "Name": {
                    "title": [{"text": {"content": name}}]
                },
                "Course Code": {
                    "rich_text": [{"text": {"content": course_code}}]
                },
                "Due Date": {
                    "date": {"start": due_date}
                },
                "Description": {
                    "rich_text": [{"text": {"content": description}}]
                },
                "Notes": {
                    "rich_text": [{"text": {"content": notes}}]
                },
                "status": {
                    "status": {"name": status}
                }
            }
        )
        return {"success": True, "message": f"Lab '{name}' added successfully!"}
    except Exception as e:
        return {"success": False, "message": f"Error adding lab: {str(e)}"}


def list_labs() -> list:
    """Get all labs sorted by due date."""
    try:
        response = notion.databases.query(
            database_id=config.LABS_DB_ID,
            sorts=[{"property": "Due Date", "direction": "ascending"}]
        )
        return _parse_items(response["results"], "lab")
    except Exception as e:
        print(f"Error listing labs: {e}")
        return []


# =============================================================================
# PROJECT OPERATIONS
# =============================================================================

def add_project(name: str, course_code: str, due_date: str, notes: str = "", status: str = "Not started") -> dict:
    """
    Add a new project to the Projects database.
    
    Args:
        name: Project name (e.g., "Final Project")
        course_code: Course code (e.g., "CS101")
        due_date: Due date in YYYY-MM-DD format
        notes: Optional notes
        status: "Not started", "In progress", or "Done"
    
    Returns:
        dict with success status and message
    """
    try:
        response = notion.pages.create(
            parent={"database_id": config.PROJECTS_DB_ID},
            properties={
                "Name": {
                    "title": [{"text": {"content": name}}]
                },
                "Course Code": {
                    "rich_text": [{"text": {"content": course_code}}]
                },
                "Due Date": {
                    "date": {"start": due_date}
                },
                "Notes": {
                    "rich_text": [{"text": {"content": notes}}]
                },
                "status": {
                    "status": {"name": status}
                }
            }
        )
        return {"success": True, "message": f"Project '{name}' added successfully!"}
    except Exception as e:
        return {"success": False, "message": f"Error adding project: {str(e)}"}


def list_projects() -> list:
    """Get all projects sorted by due date."""
    try:
        response = notion.databases.query(
            database_id=config.PROJECTS_DB_ID,
            sorts=[{"property": "Due Date", "direction": "ascending"}]
        )
        return _parse_items(response["results"], "project")
    except Exception as e:
        print(f"Error listing projects: {e}")
        return []


# =============================================================================
# COURSE OPERATIONS
# =============================================================================

def add_course(name: str, course_code: str, semester: int, professor: str = "", ects: int = 0) -> dict:
    """
    Add a new course to the Courses database.
    
    Args:
        name: Course name (e.g., "Electronics II")
        course_code: Course code (e.g., "PHY202")
        semester: Semester number
        professor: Professor name
        ects: ECTS credits
    
    Returns:
        dict with success status and message
    """
    try:
        response = notion.pages.create(
            parent={"database_id": config.COURSES_DB_ID},
            properties={
                "Name": {
                    "title": [{"text": {"content": name}}]
                },
                "Course Code": {
                    "rich_text": [{"text": {"content": course_code}}]
                },
                "Semester": {
                    "number": semester
                },
                "Professor": {
                    "rich_text": [{"text": {"content": professor}}]
                },
                "ECTS": {
                    "number": ects
                }
            }
        )
        return {"success": True, "message": f"Course '{name}' added successfully!"}
    except Exception as e:
        return {"success": False, "message": f"Error adding course: {str(e)}"}


def list_courses() -> list:
    """Get all courses sorted by semester."""
    try:
        response = notion.databases.query(
            database_id=config.COURSES_DB_ID,
            sorts=[{"property": "Semester", "direction": "ascending"}]
        )
        
        courses = []
        for page in response["results"]:
            props = page["properties"]
            courses.append({
                "id": page["id"],
                "name": _get_title(props, "Name"),
                "course_code": _get_text(props, "Course Code"),
                "semester": props.get("Semester", {}).get("number", 0),
                "professor": _get_text(props, "Professor"),
                "ects": props.get("ECTS", {}).get("number", 0)
            })
        return courses
    except Exception as e:
        print(f"Error listing courses: {e}")
        return []


# =============================================================================
# UPDATE OPERATIONS
# =============================================================================

def update_status(page_id: str, new_status: str) -> dict:
    """
    Update the status of any item (assignment, lab, or project).
    
    Args:
        page_id: Notion page ID
        new_status: "Not started", "In progress", or "Done"
    
    Returns:
        dict with success status and message
    """
    try:
        notion.pages.update(
            page_id=page_id,
            properties={
                "status": {
                    "status": {"name": new_status}
                }
            }
        )
        return {"success": True, "message": f"Status updated to '{new_status}'"}
    except Exception as e:
        return {"success": False, "message": f"Error updating status: {str(e)}"}


def update_due_date(page_id: str, new_date: str) -> dict:
    """
    Update the due date of any item.
    
    Args:
        page_id: Notion page ID
        new_date: Date in YYYY-MM-DD format
    
    Returns:
        dict with success status and message
    """
    try:
        notion.pages.update(
            page_id=page_id,
            properties={
                "Due Date": {
                    "date": {"start": new_date}
                }
            }
        )
        return {"success": True, "message": f"Due date updated to '{new_date}'"}
    except Exception as e:
        return {"success": False, "message": f"Error updating due date: {str(e)}"}


def update_course(page_id: str, new_course: str) -> dict:
    """
    Update the course code of any item.
    
    Args:
        page_id: Notion page ID
        new_course: Course code
    
    Returns:
        dict with success status and message
    """
    try:
        notion.pages.update(
            page_id=page_id,
            properties={
                "Course Code": {
                    "rich_text": [{"text": {"content": new_course}}]
                }
            }
        )
        return {"success": True, "message": f"Course updated to '{new_course}'"}
    except Exception as e:
        return {"success": False, "message": f"Error updating course: {str(e)}"}


def update_notes(page_id: str, new_notes: str) -> dict:
    """
    Update the notes of any item.
    
    Args:
        page_id: Notion page ID
        new_notes: New notes text
    
    Returns:
        dict with success status and message
    """
    try:
        notion.pages.update(
            page_id=page_id,
            properties={
                "Notes": {
                    "rich_text": [{"text": {"content": new_notes}}]
                }
            }
        )
        return {"success": True, "message": "Notes updated"}
    except Exception as e:
        return {"success": False, "message": f"Error updating notes: {str(e)}"}


def delete_item(page_id: str) -> dict:
    """
    Delete (archive) an item.
    
    Args:
        page_id: Notion page ID
    
    Returns:
        dict with success status and message
    """
    try:
        notion.pages.update(
            page_id=page_id,
            archived=True
        )
        return {"success": True, "message": "Item deleted"}
    except Exception as e:
        return {"success": False, "message": f"Error deleting item: {str(e)}"}


def get_item_by_id(page_id: str) -> dict:
    """
    Get a single item by its page ID.
    
    Args:
        page_id: Notion page ID
    
    Returns:
        dict with item details or None
    """
    try:
        page = notion.pages.retrieve(page_id=page_id)
        props = page["properties"]
        
        return {
            "id": page["id"],
            "name": _get_title(props, "Name"),
            "course_code": _get_text(props, "Course Code"),
            "due_date": _get_date(props, "Due Date"),
            "notes": _get_text(props, "Notes"),
            "status": _get_status(props, "status")
        }
    except Exception as e:
        print(f"Error getting item: {e}")
        return None


# =============================================================================
# QUERY OPERATIONS
# =============================================================================

def get_upcoming(days: int = 7) -> dict:
    """
    Get all upcoming work within specified days.
    
    Args:
        days: Number of days to look ahead
    
    Returns:
        dict with assignments, labs, and projects
    """
    today = datetime.now().date().isoformat()
    future_date = (datetime.now().date() + timedelta(days=days)).isoformat()
    
    date_filter = {
        "and": [
            {"property": "Due Date", "date": {"on_or_after": today}},
            {"property": "Due Date", "date": {"on_or_before": future_date}}
        ]
    }
    
    upcoming = {
        "assignments": [],
        "labs": [],
        "projects": []
    }
    
    # Query each database
    db_configs = [
        ("assignments", config.ASSIGNMENTS_DB_ID, "assignment"),
        ("labs", config.LABS_DB_ID, "lab"),
        ("projects", config.PROJECTS_DB_ID, "project")
    ]
    
    for key, db_id, item_type in db_configs:
        try:
            response = notion.databases.query(
                database_id=db_id,
                filter=date_filter,
                sorts=[{"property": "Due Date", "direction": "ascending"}]
            )
            upcoming[key] = _parse_items(response["results"], item_type)
        except Exception as e:
            print(f"Error querying {key}: {e}")
    
    return upcoming


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _get_title(props: dict, prop_name: str) -> str:
    """Extract title property value."""
    try:
        return props[prop_name]["title"][0]["text"]["content"]
    except (KeyError, IndexError):
        return "Untitled"


def _get_text(props: dict, prop_name: str) -> str:
    """Extract rich_text property value."""
    try:
        return props[prop_name]["rich_text"][0]["text"]["content"]
    except (KeyError, IndexError):
        return ""


def _get_date(props: dict, prop_name: str) -> str:
    """Extract date property value."""
    try:
        return props[prop_name]["date"]["start"]
    except (KeyError, TypeError):
        return "No date"


def _get_status(props: dict, prop_name: str) -> str:
    """Extract status property value."""
    try:
        return props[prop_name]["status"]["name"]
    except (KeyError, TypeError):
        return "Not started"


def _parse_items(results: list, item_type: str) -> list:
    """Parse Notion query results into clean dictionaries."""
    items = []
    for page in results:
        props = page["properties"]
        item = {
            "id": page["id"],
            "name": _get_title(props, "Name"),
            "course_code": _get_text(props, "Course Code"),
            "due_date": _get_date(props, "Due Date"),
            "notes": _get_text(props, "Notes"),
            "status": _get_status(props, "status")
        }
        
        # Add description for labs
        if item_type == "lab":
            item["description"] = _get_text(props, "Description")
        
        items.append(item)
    return items


# =============================================================================
# TEST FUNCTION
# =============================================================================

def test_connection() -> bool:
    """Test Notion API connection."""
    try:
        notion.databases.retrieve(database_id=config.ASSIGNMENTS_DB_ID)
        print("✅ Connected to Notion successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to connect to Notion: {e}")
        return False


if __name__ == "__main__":
    test_connection()