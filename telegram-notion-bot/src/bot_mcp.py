"""
Telegram Bot that uses Claude with MCP server for Notion operations
"""

import asyncio
import subprocess
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from anthropic import Anthropic
import config

# Initialize Anthropic client
anthropic_client = Anthropic(api_key=config.ANTHROPIC_API_KEY)

# Global variable to store MCP server process
mcp_process = None


async def start_mcp_server():
    """Start the MCP server as a subprocess"""
    global mcp_process
    try:
        mcp_process = subprocess.Popen(
            ["python", "src/mcp_server.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        print("✅ MCP Server started successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to start MCP server: {e}")
        return False


async def call_claude_with_mcp(user_message: str) -> str:
    """
    Send a message to Claude with MCP tools available
    
    Args:
        user_message: The user's message/request
    
    Returns:
        Claude's response as a string
    """
    try:
        # Import Notion functions from mcp_server
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
        from mcp_server import add_assignment, add_lab, add_project, query_upcoming_work, list_all_from_database
        
        # Define tools for Claude
        tools = [
            {
                "name": "add_assignment",
                "description": "Add a new assignment to the Assignments database in Notion",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Assignment title"},
                        "course": {"type": "string", "description": "Course code (e.g., CS101)"},
                        "due_date": {"type": "string", "description": "Due date in YYYY-MM-DD format"},
                        "notes": {"type": "string", "description": "Optional notes"},
                        "status": {"type": "string", "enum": ["Not started", "In progress", "Done"]}
                    },
                    "required": ["title", "course", "due_date"]
                }
            },
            {
                "name": "add_lab",
                "description": "Add a new lab to the Labs database in Notion",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Lab title"},
                        "course": {"type": "string", "description": "Course code"},
                        "due_date": {"type": "string", "description": "Due date in YYYY-MM-DD format"},
                        "notes": {"type": "string", "description": "Optional notes"}
                    },
                    "required": ["title", "course", "due_date"]
                }
            },
            {
                "name": "add_project",
                "description": "Add a new project to the Projects database",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Project title"},
                        "course": {"type": "string", "description": "Course code"},
                        "due_date": {"type": "string", "description": "Due date in YYYY-MM-DD format"},
                        "notes": {"type": "string", "description": "Optional notes"}
                    },
                    "required": ["title", "course", "due_date"]
                }
            },
            {
                "name": "query_upcoming_work",
                "description": "Query all upcoming work within specified days",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "days": {"type": "number", "description": "Number of days to look ahead (default: 7)"}
                    }
                }
            }
        ]
        
        messages = [{"role": "user", "content": user_message}]
        
        # Initial call to Claude with tools
        response = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            system="""You are a helpful virtual secretary managing a student's Notion databases. 
Use the tools available to actually perform actions in Notion. When the user asks to add something, use the appropriate tool.
Be conversational and confirm what you've done.""",
            messages=messages,
            tools=tools
        )
        
        # Check if Claude wants to use tools
        while response.stop_reason == "tool_use":
            # Process tool calls
            tool_results = []
            
            for content_block in response.content:
                if content_block.type == "tool_use":
                    tool_name = content_block.name
                    tool_input = content_block.input
                    
                    print(f"🔧 Claude is calling tool: {tool_name} with {tool_input}")
                    
                    # Execute the tool
                    try:
                        if tool_name == "add_assignment":
                            result = add_assignment(
                                title=tool_input["title"],
                                course=tool_input["course"],
                                due_date=tool_input["due_date"],
                                notes=tool_input.get("notes", ""),
                                status=tool_input.get("status", "Not started")
                            )
                            tool_result = f"✅ Assignment added successfully"
                        
                        elif tool_name == "add_lab":
                            result = add_lab(
                                title=tool_input["title"],
                                course=tool_input["course"],
                                due_date=tool_input["due_date"],
                                notes=tool_input.get("notes", "")
                            )
                            tool_result = f"✅ Lab added successfully"
                        
                        elif tool_name == "add_project":
                            result = add_project(
                                title=tool_input["title"],
                                course=tool_input["course"],
                                due_date=tool_input["due_date"],
                                notes=tool_input.get("notes", "")
                            )
                            tool_result = f"✅ Project added successfully"
                        
                        elif tool_name == "query_upcoming_work":
                            days = tool_input.get("days", 7)
                            result = query_upcoming_work(days)
                            tool_result = json.dumps(result, indent=2)
                        
                        else:
                            tool_result = f"Unknown tool: {tool_name}"
                    
                    except Exception as e:
                        tool_result = f"❌ Error: {str(e)}"
                    
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": content_block.id,
                        "content": tool_result
                    })
            
            # Add assistant response and tool results to messages
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
            
            # Get Claude's next response
            response = anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                system="""You are a helpful virtual secretary managing a student's Notion databases. 
Use the tools available to actually perform actions in Notion. When the user asks to add something, use the appropriate tool.
Be conversational and confirm what you've done.""",
                messages=messages,
                tools=tools
            )
        
        # Extract final text response
        final_response = ""
        for content_block in response.content:
            if hasattr(content_block, "text"):
                final_response += content_block.text
        
        return final_response
        
    except Exception as e:
        return f"❌ Error communicating with Claude: {str(e)}"


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    welcome_message = """
👋 Welcome to your Virtual Secretary!

I'm Claude, and I can help you manage your university work in Notion.

You can talk to me naturally! For example:
- "Add an assignment for CS101 due next Friday called Homework 3"
- "What's due this week?"
- "Add a lab for PHY202 due on November 30th"
- "Show me all my assignments"

Just chat with me like you would with a real secretary! 📚
    """
    await update.message.reply_text(welcome_message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = """
🤖 **How to use me:**

Just talk naturally! I understand requests like:

**Adding work:**
- "Add assignment Homework 3 for CS101 due November 25"
- "I have a lab for PHY202 due next Wednesday"
- "Add project Final Project for ENG201 due December 15"

**Querying work:**
- "What's due this week?"
- "Show me upcoming work"
- "What assignments do I have?"
- "List all my labs"

**Tips:**
- You can use natural date formats (tomorrow, next Friday, Nov 25, 2024-11-25)
- I'll ask for clarification if I need more info
- Be specific about course codes and titles

Need help? Just ask! 💬
    """
    await update.message.reply_text(help_text)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle regular text messages from user
    This is where the magic happens - send to Claude with MCP tools
    """
    user_message = update.message.text
    user_name = update.effective_user.first_name
    
    # Show typing indicator
    await update.message.chat.send_action("typing")
    
    # Get response from Claude (with MCP tools)
    claude_response = await call_claude_with_mcp(user_message)
    
    # Send response back to user
    await update.message.reply_text(claude_response)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    print(f"Update {update} caused error {context.error}")
    if update and update.message:
        await update.message.reply_text("❌ Sorry, something went wrong. Please try again.")


async def post_init(application: Application):
    """Initialize after bot starts"""
    print("🤖 Bot is starting up...")
    # Start MCP server
    await start_mcp_server()
    print("✅ Bot is ready!")


async def post_shutdown(application: Application):
    """Cleanup when bot shuts down"""
    global mcp_process
    if mcp_process:
        mcp_process.terminate()
        print("🛑 MCP server stopped")


def main():
    """Start the bot"""
    # Validate configuration
    try:
        config.validate_config()
        
        if not config.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not found in .env file")
        
        print("✅ Configuration validated")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return
    
    # Create the Application
    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).post_init(post_init).post_shutdown(post_shutdown).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start the bot
    print("🚀 Starting Telegram bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()