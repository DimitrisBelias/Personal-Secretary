"""
MCP Server for Notion Integration
Exposes Notion database operations as tools that Claude can use
"""

import asyncio
import json
from datetime import datetime, timedelta
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from notion_client import Client
import config

# Initialize Notion client
notion = Client(auth=config.NOTION_TOKEN)

# Create MCP server
server = Server("notion-student-planner")


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """
    List all available tools for Claude to use
    """
    return [
        Tool(
            name="add_assignment",
            description="Add a new assignment to the Assignments database in Notion",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "The title of the assignment (e.g., 'Homework 3')"
                    },
                    "course": {
                        "type": "string",
                        "description": "The course code (e.g., 'PHY202', 'CS101')"
                    },
                    "due_date": {
                        "type": "string",
                        "description": "Due date in YYYY-MM-DD format (e.g., '2024-11-25')"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Optional notes about the assignment"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["Not started", "In progress", "Done"],
                        "description": "Current status of the assignment"
                    }
                },
                "required": ["title", "course", "due_date"]
            }
        ),
        Tool(
            name="add_lab",
            description="Add a new lab to the Labs database in Notion",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "The title of the lab"
                    },
                    "course": {
                        "type": "string",
                        "description": "The course code"
                    },
                    "due_date": {
                        "type": "string",
                        "description": "Due date in YYYY-MM-DD format"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Optional notes about the lab"
                    }
                },
                "required": ["title", "course", "due_date"]
            }
        ),
        Tool(
            name="add_project",
            description="Add a new project to the Projects database in Notion",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "The title of the project"
                    },
                    "course": {
                        "type": "string",
                        "description": "The course code"
                    },
                    "due_date": {
                        "type": "string",
                        "description": "Due date in YYYY-MM-DD format"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Optional notes about the project"
                    }
                },
                "required": ["title", "course", "due_date"]
            }
        ),
        Tool(
            name="query_upcoming_work",
            description="Query all upcoming work (assignments, labs, projects) from Notion within a specified number of days",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {
                        "type": "number",
                        "description": "Number of days to look ahead (default: 7)"
                    }
                }
            }
        ),
        Tool(
            name="list_assignments",
            description="List all assignments from the Assignments database",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="list_labs",
            description="List all labs from the Labs database",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="list_projects",
            description="List all projects from the Projects database",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """
    Handle tool calls from Claude
    """
    try:
        if name == "add_assignment":
            result = add_assignment(
                title=arguments["title"],
                course=arguments["course"],
                due_date=arguments["due_date"],
                notes=arguments.get("notes", ""),
                status=arguments.get("status", "Not started")
            )
            return [TextContent(
                type="text",
                text=f"✅ Assignment '{arguments['title']}' added successfully for {arguments['course']}, due {arguments['due_date']}"
            )]
        
        elif name == "add_lab":
            result = add_lab(
                title=arguments["title"],
                course=arguments["course"],
                due_date=arguments["due_date"],
                notes=arguments.get("notes", "")
            )
            return [TextContent(
                type="text",
                text=f"✅ Lab '{arguments['title']}' added successfully for {arguments['course']}, due {arguments['due_date']}"
            )]
        
        elif name == "add_project":
            result = add_project(
                title=arguments["title"],
                course=arguments["course"],
                due_date=arguments["due_date"],
                notes=arguments.get("notes", "")
            )
            return [TextContent(
                type="text",
                text=f"✅ Project '{arguments['title']}' added successfully for {arguments['course']}, due {arguments['due_date']}"
            )]
        
        elif name == "query_upcoming_work":
            days = arguments.get("days", 7)
            work = query_upcoming_work(days)
            return [TextContent(
                type="text",
                text=json.dumps(work, indent=2)
            )]
        
        elif name == "list_assignments":
            assignments = list_all_from_database(config.ASSIGNMENTS_DB_ID)
            return [TextContent(
                type="text",
                text=json.dumps(assignments, indent=2)
            )]
        
        elif name == "list_labs":
            labs = list_all_from_database(config.LABS_DB_ID)
            return [TextContent(
                type="text",
                text=json.dumps(labs, indent=2)
            )]
        
        elif name == "list_projects":
            projects = list_all_from_database(config.PROJECTS_DB_ID)
            return [TextContent(
                type="text",
                text=json.dumps(projects, indent=2)
            )]
        
        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]
    
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error executing tool {name}: {str(e)}"
        )]


# Notion helper functions
def add_assignment(title, course, due_date, notes="", status="Not started"):
    """Add assignment to Notion"""
    try:
        notion.pages.create(
            parent={"database_id": config.ASSIGNMENTS_DB_ID},
            properties={
                "Title": {
                    "title": [{"text": {"content": title}}]
                },
                "Due Date": {
                    "date": {"start": due_date}
                },
                "Course Code": {
                    "rich_text": [{"text": {"content": course}}]
                },
                "Notes": {
                    "rich_text": [{"text": {"content": notes}}]
                },
                "status": {
                    "status": {"name": status}
                }
            }
        )
        return True
    except Exception as e:
        print(f"Error adding assignment: {e}")
        raise


def add_lab(title, course, due_date, notes=""):
    """Add lab to Notion"""
    try:
        notion.pages.create(
            parent={"database_id": config.LABS_DB_ID},
            properties={
                "Title": {
                    "title": [{"text": {"content": title}}]
                },
                "Due Date": {
                    "date": {"start": due_date}
                },
                "Course Code": {
                    "rich_text": [{"text": {"content": course}}]
                },
                "Notes": {
                    "rich_text": [{"text": {"content": notes}}]
                }
            }
        )
        return True
    except Exception as e:
        print(f"Error adding lab: {e}")
        raise


def add_project(title, course, due_date, notes=""):
    """Add project to Notion"""
    try:
        notion.pages.create(
            parent={"database_id": config.PROJECTS_DB_ID},
            properties={
                "Title": {
                    "title": [{"text": {"content": title}}]
                },
                "Due Date": {
                    "date": {"start": due_date}
                },
                "Course Code": {
                    "rich_text": [{"text": {"content": course}}]
                },
                "Notes": {
                    "rich_text": [{"text": {"content": notes}}]
                }
            }
        )
        return True
    except Exception as e:
        print(f"Error adding project: {e}")
        raise


def query_upcoming_work(days=7):
    """Query upcoming work from all databases"""
    today = datetime.now().date().isoformat()
    future_date = (datetime.now().date() + timedelta(days=days)).isoformat()
    
    all_work = {
        "assignments": [],
        "labs": [],
        "projects": []
    }
    
    # Query each database
    for db_type, db_id in [
        ("assignments", config.ASSIGNMENTS_DB_ID),
        ("labs", config.LABS_DB_ID),
        ("projects", config.PROJECTS_DB_ID)
    ]:
        try:
            response = notion.databases.query(
                database_id=db_id,
                filter={
                    "and": [
                        {"property": "Due Date", "date": {"on_or_after": today}},
                        {"property": "Due Date", "date": {"on_or_before": future_date}}
                    ]
                },
                sorts=[{"property": "Due Date", "direction": "ascending"}]
            )
            
            for page in response["results"]:
                props = page["properties"]
                item = {
                    "title": props["Title"]["title"][0]["text"]["content"] if props["Title"]["title"] else "Untitled",
                    "course": props["Course Code"]["rich_text"][0]["text"]["content"] if props["Course Code"]["rich_text"] else "N/A",
                    "due_date": props["Due Date"]["date"]["start"] if props["Due Date"]["date"] else "No date"
                }
                all_work[db_type].append(item)
        except Exception as e:
            print(f"Error querying {db_type}: {e}")
    
    return all_work


def list_all_from_database(database_id):
    """List all items from a database"""
    try:
        response = notion.databases.query(
            database_id=database_id,
            sorts=[{"property": "Due Date", "direction": "ascending"}]
        )
        
        items = []
        for page in response["results"]:
            props = page["properties"]
            item = {
                "title": props["Title"]["title"][0]["text"]["content"] if props["Title"]["title"] else "Untitled",
                "course": props["Course Code"]["rich_text"][0]["text"]["content"] if props["Course Code"]["rich_text"] else "N/A",
                "due_date": props["Due Date"]["date"]["start"] if props["Due Date"]["date"] else "No date"
            }
            items.append(item)
        
        return items
    except Exception as e:
        print(f"Error listing from database: {e}")
        return []


async def main():
    """Run the MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="notion-student-planner",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )


if __name__ == "__main__":
    asyncio.run(main())