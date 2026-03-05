"""
Telegram Bot - Personal Secretary for University Work
Interactive button-based interface with conversation flows
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from datetime import datetime, timedelta
import os
import config
import notion_service


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _status_emoji(status: str) -> str:
    """Return emoji based on status."""
    return {
        "Not started": "⚪",
        "In progress": "🔵",
        "Done": "✅"
    }.get(status, "⚪")


# =============================================================================
# CONVERSATION STATES
# =============================================================================

# Main states
MAIN_MENU = 0

# Add flow states
ADD_MENU = 10
ADD_ASSIGNMENT_NAME = 11
ADD_ASSIGNMENT_COURSE = 12
ADD_ASSIGNMENT_DATE = 13
ADD_ASSIGNMENT_NOTES = 14

ADD_LAB_NAME = 20
ADD_LAB_COURSE = 21
ADD_LAB_DATE = 22
ADD_LAB_DESCRIPTION = 23
ADD_LAB_NOTES = 24

ADD_PROJECT_NAME = 30
ADD_PROJECT_COURSE = 31
ADD_PROJECT_DATE = 32
ADD_PROJECT_NOTES = 33

ADD_COURSE_NAME = 40
ADD_COURSE_CODE = 41
ADD_COURSE_SEMESTER = 42
ADD_COURSE_PROFESSOR = 43
ADD_COURSE_ECTS = 44

# List states
LIST_MENU = 50
LIST_ASSIGNMENTS_SELECT = 51
LIST_LABS_SELECT = 52
LIST_PROJECTS_SELECT = 53
ITEM_ACTION = 54
EDIT_DATE = 55
EDIT_COURSE = 56
EDIT_NOTES = 57
CONFIRM_DELETE = 58

# Upcoming states
UPCOMING_MENU = 60


# =============================================================================
# KEYBOARD BUILDERS
# =============================================================================

def main_menu_keyboard():
    """Build main menu keyboard."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ Add", callback_data="menu_add"),
            InlineKeyboardButton("📋 List", callback_data="menu_list"),
            InlineKeyboardButton("📅 Upcoming", callback_data="menu_upcoming"),
        ]
    ])


def add_menu_keyboard():
    """Build add menu keyboard."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📝 Assignment", callback_data="add_assignment"),
            InlineKeyboardButton("🔬 Lab", callback_data="add_lab"),
        ],
        [
            InlineKeyboardButton("🎯 Project", callback_data="add_project"),
            InlineKeyboardButton("📖 Course", callback_data="add_course"),
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="back_main")]
    ])


def list_menu_keyboard():
    """Build list menu keyboard."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📝 Assignments", callback_data="list_assignments"),
            InlineKeyboardButton("🔬 Labs", callback_data="list_labs"),
        ],
        [
            InlineKeyboardButton("🎯 Projects", callback_data="list_projects"),
            InlineKeyboardButton("📖 Courses", callback_data="list_courses"),
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="back_main")]
    ])


def items_list_keyboard(items: list, item_type: str):
    """Build keyboard with clickable items for status update."""
    buttons = []
    
    for item in items:
        if not item.get('name') or item['name'] == "Untitled":
            continue
        
        emoji = _status_emoji(item.get("status", "Not started"))
        btn_text = f"{emoji} {item['name']} ({item['course_code']})"
        btn_data = f"{item_type}_{item['id'][:32]}"
        buttons.append([InlineKeyboardButton(btn_text, callback_data=btn_data)])
    
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="back_list")])
    
    return InlineKeyboardMarkup(buttons)


def item_action_keyboard(item_id: str, item_type: str):
    """Build keyboard for item actions (edit, delete, status)."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⚪ Not Started", callback_data=f"status_{item_type}_{item_id}_Not started"),
            InlineKeyboardButton("🔵 In Progress", callback_data=f"status_{item_type}_{item_id}_In progress"),
            InlineKeyboardButton("✅ Done", callback_data=f"status_{item_type}_{item_id}_Done"),
        ],
        [
            InlineKeyboardButton("📅 Change Date", callback_data=f"editdate_{item_type}_{item_id}"),
            InlineKeyboardButton("📚 Change Course", callback_data=f"editcourse_{item_type}_{item_id}"),
        ],
        [
            InlineKeyboardButton("✏️ Edit Notes", callback_data=f"editnotes_{item_type}_{item_id}"),
            InlineKeyboardButton("🗑️ Delete", callback_data=f"delete_{item_type}_{item_id}"),
        ],
        [InlineKeyboardButton("🔙 Back", callback_data=f"back_{item_type}s")]
    ])


def confirm_delete_keyboard(item_id: str, item_type: str):
    """Build confirmation keyboard for delete action."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Yes, Delete", callback_data=f"confirmdelete_{item_type}_{item_id}"),
            InlineKeyboardButton("❌ Cancel", callback_data=f"canceldelete_{item_type}_{item_id}"),
        ]
    ])


def upcoming_menu_keyboard():
    """Build upcoming menu keyboard."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("7 Days", callback_data="upcoming_7"),
            InlineKeyboardButton("14 Days", callback_data="upcoming_14"),
            InlineKeyboardButton("30 Days", callback_data="upcoming_30"),
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="back_main")]
    ])


def courses_keyboard():
    """Build keyboard with courses from Notion."""
    courses = notion_service.list_courses()
    buttons = []
    
    for course in courses:
        if not course['name'] or course['name'] == "Untitled" or not course['course_code']:
            continue
            
        btn_text = f"{course['course_code']} - {course['name']}"
        btn_data = f"course_{course['course_code']}"
        buttons.append([InlineKeyboardButton(btn_text, callback_data=btn_data)])
    
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="back_add")])
    
    return InlineKeyboardMarkup(buttons)


def date_keyboard():
    """Build date selection keyboard."""
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    next_week = today + timedelta(days=7)
    
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"📅 Today ({today.strftime('%d/%m')})", callback_data=f"date_{today.isoformat()}"),
            InlineKeyboardButton(f"📅 Tomorrow ({tomorrow.strftime('%d/%m')})", callback_data=f"date_{tomorrow.isoformat()}"),
        ],
        [
            InlineKeyboardButton(f"📅 Next Week ({next_week.strftime('%d/%m')})", callback_data=f"date_{next_week.isoformat()}"),
            InlineKeyboardButton("✏️ Custom", callback_data="date_custom"),
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="back_add")]
    ])


def skip_keyboard():
    """Build skip/back keyboard for optional fields."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⏭️ Skip", callback_data="skip"),
            InlineKeyboardButton("🔙 Back", callback_data="back_add"),
        ]
    ])


def done_keyboard():
    """Build keyboard shown after successful action."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ Add Another", callback_data="menu_add"),
            InlineKeyboardButton("📋 List", callback_data="menu_list"),
        ],
        [InlineKeyboardButton("🏠 Menu", callback_data="back_main")]
    ])


def back_keyboard(callback_data: str):
    """Build simple back button keyboard."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data=callback_data)]
    ])


# =============================================================================
# MAIN MENU HANDLERS
# =============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command - show main menu."""
    context.user_data.clear()
    
    welcome = "👋 Welcome to your Personal Secretary!\n\nWhat would you like to do?"
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(welcome, reply_markup=main_menu_keyboard())
    else:
        await update.message.reply_text(welcome, reply_markup=main_menu_keyboard())
    
    return MAIN_MENU


async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle main menu button presses."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "menu_add":
        await query.edit_message_text("What would you like to add?", reply_markup=add_menu_keyboard())
        return ADD_MENU
    
    elif query.data == "menu_list":
        await query.edit_message_text("What would you like to see?", reply_markup=list_menu_keyboard())
        return LIST_MENU
    
    elif query.data == "menu_upcoming":
        await query.edit_message_text("Show upcoming work for:", reply_markup=upcoming_menu_keyboard())
        return UPCOMING_MENU
    
    return MAIN_MENU


# =============================================================================
# ADD MENU HANDLERS
# =============================================================================

async def add_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle add menu selections."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "back_main":
        return await start(update, context)
    
    elif query.data == "add_assignment":
        await query.edit_message_text("📝 What's the assignment name?", reply_markup=back_keyboard("back_add"))
        return ADD_ASSIGNMENT_NAME
    
    elif query.data == "add_lab":
        await query.edit_message_text("🔬 What's the lab name?", reply_markup=back_keyboard("back_add"))
        return ADD_LAB_NAME
    
    elif query.data == "add_project":
        await query.edit_message_text("🎯 What's the project name?", reply_markup=back_keyboard("back_add"))
        return ADD_PROJECT_NAME
    
    elif query.data == "add_course":
        await query.edit_message_text("📖 What's the course name?", reply_markup=back_keyboard("back_add"))
        return ADD_COURSE_NAME
    
    return ADD_MENU


async def back_to_add_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Go back to add menu."""
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    await query.edit_message_text("What would you like to add?", reply_markup=add_menu_keyboard())
    return ADD_MENU


# =============================================================================
# ADD ASSIGNMENT FLOW
# =============================================================================

async def add_assignment_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle assignment name input."""
    if update.callback_query:
        if update.callback_query.data == "back_add":
            return await back_to_add_menu(update, context)
    
    context.user_data["assignment_name"] = update.message.text
    
    courses = notion_service.list_courses()
    if not courses:
        await update.message.reply_text(
            "⚠️ No courses found in Notion!\n\nPlease add a course first.",
            reply_markup=add_menu_keyboard()
        )
        return ADD_MENU
    
    await update.message.reply_text("📚 Select the course:", reply_markup=courses_keyboard())
    return ADD_ASSIGNMENT_COURSE


async def add_assignment_course(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle assignment course selection."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "back_add":
        return await back_to_add_menu(update, context)
    
    course_code = query.data.replace("course_", "")
    context.user_data["assignment_course"] = course_code
    
    await query.edit_message_text(f"📅 When is it due?\n\nCourse: {course_code}", reply_markup=date_keyboard())
    return ADD_ASSIGNMENT_DATE


async def add_assignment_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle assignment date selection."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "back_add":
        return await back_to_add_menu(update, context)
    
    if query.data == "date_custom":
        await query.edit_message_text(
            "📅 Enter the due date (YYYY-MM-DD format):\n\nExample: 2025-12-20",
            reply_markup=back_keyboard("back_add")
        )
        return ADD_ASSIGNMENT_DATE
    
    due_date = query.data.replace("date_", "")
    context.user_data["assignment_date"] = due_date
    
    await query.edit_message_text(
        f"📝 Any notes for this assignment?\n\n"
        f"Name: {context.user_data['assignment_name']}\n"
        f"Course: {context.user_data['assignment_course']}\n"
        f"Due: {due_date}",
        reply_markup=skip_keyboard()
    )
    return ADD_ASSIGNMENT_NOTES


async def add_assignment_date_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle custom date text input for assignment."""
    date_text = update.message.text.strip()
    
    try:
        datetime.strptime(date_text, "%Y-%m-%d")
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid date format. Please use YYYY-MM-DD\n\nExample: 2025-12-20",
            reply_markup=back_keyboard("back_add")
        )
        return ADD_ASSIGNMENT_DATE
    
    context.user_data["assignment_date"] = date_text
    
    await update.message.reply_text(
        f"📝 Any notes for this assignment?\n\n"
        f"Name: {context.user_data['assignment_name']}\n"
        f"Course: {context.user_data['assignment_course']}\n"
        f"Due: {date_text}",
        reply_markup=skip_keyboard()
    )
    return ADD_ASSIGNMENT_NOTES


async def add_assignment_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle assignment notes input and save to Notion."""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        
        if query.data == "back_add":
            return await back_to_add_menu(update, context)
        
        if query.data == "skip":
            notes = ""
        else:
            return ADD_ASSIGNMENT_NOTES
    else:
        notes = update.message.text
    
    result = notion_service.add_assignment(
        name=context.user_data["assignment_name"],
        course_code=context.user_data["assignment_course"],
        due_date=context.user_data["assignment_date"],
        notes=notes
    )
    
    if result["success"]:
        response = (
            f"✅ Assignment added!\n\n"
            f"📝 {context.user_data['assignment_name']}\n"
            f"📚 {context.user_data['assignment_course']}\n"
            f"📅 {context.user_data['assignment_date']}\n"
            f"📌 {notes if notes else 'No notes'}"
        )
    else:
        response = f"❌ Error: {result['message']}"
    
    context.user_data.clear()
    
    if update.callback_query:
        await update.callback_query.edit_message_text(response, reply_markup=done_keyboard())
    else:
        await update.message.reply_text(response, reply_markup=done_keyboard())
    
    return MAIN_MENU


# =============================================================================
# ADD LAB FLOW
# =============================================================================

async def add_lab_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle lab name input."""
    if update.callback_query:
        if update.callback_query.data == "back_add":
            return await back_to_add_menu(update, context)
    
    context.user_data["lab_name"] = update.message.text
    
    courses = notion_service.list_courses()
    if not courses:
        await update.message.reply_text(
            "⚠️ No courses found! Please add a course first.",
            reply_markup=add_menu_keyboard()
        )
        return ADD_MENU
    
    await update.message.reply_text("📚 Select the course:", reply_markup=courses_keyboard())
    return ADD_LAB_COURSE


async def add_lab_course(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle lab course selection."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "back_add":
        return await back_to_add_menu(update, context)
    
    course_code = query.data.replace("course_", "")
    context.user_data["lab_course"] = course_code
    
    await query.edit_message_text(f"📅 When is it due?", reply_markup=date_keyboard())
    return ADD_LAB_DATE


async def add_lab_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle lab date selection."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "back_add":
        return await back_to_add_menu(update, context)
    
    if query.data == "date_custom":
        await query.edit_message_text(
            "📅 Enter the due date (YYYY-MM-DD):",
            reply_markup=back_keyboard("back_add")
        )
        return ADD_LAB_DATE
    
    due_date = query.data.replace("date_", "")
    context.user_data["lab_date"] = due_date
    
    await query.edit_message_text("📋 Lab description? (or skip)", reply_markup=skip_keyboard())
    return ADD_LAB_DESCRIPTION


async def add_lab_date_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle custom date text input for lab."""
    date_text = update.message.text.strip()
    
    try:
        datetime.strptime(date_text, "%Y-%m-%d")
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid format. Use YYYY-MM-DD",
            reply_markup=back_keyboard("back_add")
        )
        return ADD_LAB_DATE
    
    context.user_data["lab_date"] = date_text
    await update.message.reply_text("📋 Lab description? (or skip)", reply_markup=skip_keyboard())
    return ADD_LAB_DESCRIPTION


async def add_lab_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle lab description input."""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        
        if query.data == "back_add":
            return await back_to_add_menu(update, context)
        
        if query.data == "skip":
            context.user_data["lab_description"] = ""
            await query.edit_message_text("📝 Any notes?", reply_markup=skip_keyboard())
            return ADD_LAB_NOTES
    else:
        context.user_data["lab_description"] = update.message.text
        await update.message.reply_text("📝 Any notes?", reply_markup=skip_keyboard())
        return ADD_LAB_NOTES
    
    return ADD_LAB_DESCRIPTION


async def add_lab_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle lab notes and save to Notion."""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        
        if query.data == "back_add":
            return await back_to_add_menu(update, context)
        
        if query.data == "skip":
            notes = ""
        else:
            return ADD_LAB_NOTES
    else:
        notes = update.message.text
    
    result = notion_service.add_lab(
        name=context.user_data["lab_name"],
        course_code=context.user_data["lab_course"],
        due_date=context.user_data["lab_date"],
        description=context.user_data.get("lab_description", ""),
        notes=notes
    )
    
    if result["success"]:
        response = (
            f"✅ Lab added!\n\n"
            f"🔬 {context.user_data['lab_name']}\n"
            f"📚 {context.user_data['lab_course']}\n"
            f"📅 {context.user_data['lab_date']}"
        )
    else:
        response = f"❌ Error: {result['message']}"
    
    context.user_data.clear()
    
    if update.callback_query:
        await update.callback_query.edit_message_text(response, reply_markup=done_keyboard())
    else:
        await update.message.reply_text(response, reply_markup=done_keyboard())
    
    return MAIN_MENU


# =============================================================================
# ADD PROJECT FLOW
# =============================================================================

async def add_project_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle project name input."""
    if update.callback_query:
        if update.callback_query.data == "back_add":
            return await back_to_add_menu(update, context)
    
    context.user_data["project_name"] = update.message.text
    
    courses = notion_service.list_courses()
    if not courses:
        await update.message.reply_text(
            "⚠️ No courses found! Please add a course first.",
            reply_markup=add_menu_keyboard()
        )
        return ADD_MENU
    
    await update.message.reply_text("📚 Select the course:", reply_markup=courses_keyboard())
    return ADD_PROJECT_COURSE


async def add_project_course(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle project course selection."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "back_add":
        return await back_to_add_menu(update, context)
    
    course_code = query.data.replace("course_", "")
    context.user_data["project_course"] = course_code
    
    await query.edit_message_text("📅 When is it due?", reply_markup=date_keyboard())
    return ADD_PROJECT_DATE


async def add_project_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle project date selection."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "back_add":
        return await back_to_add_menu(update, context)
    
    if query.data == "date_custom":
        await query.edit_message_text(
            "📅 Enter the due date (YYYY-MM-DD):",
            reply_markup=back_keyboard("back_add")
        )
        return ADD_PROJECT_DATE
    
    due_date = query.data.replace("date_", "")
    context.user_data["project_date"] = due_date
    
    await query.edit_message_text("📝 Any notes?", reply_markup=skip_keyboard())
    return ADD_PROJECT_NOTES


async def add_project_date_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle custom date text input for project."""
    date_text = update.message.text.strip()
    
    try:
        datetime.strptime(date_text, "%Y-%m-%d")
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid format. Use YYYY-MM-DD",
            reply_markup=back_keyboard("back_add")
        )
        return ADD_PROJECT_DATE
    
    context.user_data["project_date"] = date_text
    await update.message.reply_text("📝 Any notes?", reply_markup=skip_keyboard())
    return ADD_PROJECT_NOTES


async def add_project_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle project notes and save to Notion."""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        
        if query.data == "back_add":
            return await back_to_add_menu(update, context)
        
        if query.data == "skip":
            notes = ""
        else:
            return ADD_PROJECT_NOTES
    else:
        notes = update.message.text
    
    result = notion_service.add_project(
        name=context.user_data["project_name"],
        course_code=context.user_data["project_course"],
        due_date=context.user_data["project_date"],
        notes=notes
    )
    
    if result["success"]:
        response = (
            f"✅ Project added!\n\n"
            f"🎯 {context.user_data['project_name']}\n"
            f"📚 {context.user_data['project_course']}\n"
            f"📅 {context.user_data['project_date']}"
        )
    else:
        response = f"❌ Error: {result['message']}"
    
    context.user_data.clear()
    
    if update.callback_query:
        await update.callback_query.edit_message_text(response, reply_markup=done_keyboard())
    else:
        await update.message.reply_text(response, reply_markup=done_keyboard())
    
    return MAIN_MENU


# =============================================================================
# ADD COURSE FLOW
# =============================================================================

async def add_course_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle course name input."""
    if update.callback_query:
        if update.callback_query.data == "back_add":
            return await back_to_add_menu(update, context)
    
    context.user_data["course_name"] = update.message.text
    await update.message.reply_text("🔤 What's the course code? (e.g., PHY202)", reply_markup=back_keyboard("back_add"))
    return ADD_COURSE_CODE


async def add_course_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle course code input."""
    if update.callback_query:
        if update.callback_query.data == "back_add":
            return await back_to_add_menu(update, context)
    
    context.user_data["course_code"] = update.message.text.upper()
    await update.message.reply_text("📅 Which semester? (number)", reply_markup=back_keyboard("back_add"))
    return ADD_COURSE_SEMESTER


async def add_course_semester(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle course semester input."""
    if update.callback_query:
        if update.callback_query.data == "back_add":
            return await back_to_add_menu(update, context)
    
    try:
        semester = int(update.message.text)
        context.user_data["course_semester"] = semester
        await update.message.reply_text("👨‍🏫 Professor name?", reply_markup=skip_keyboard())
        return ADD_COURSE_PROFESSOR
    except ValueError:
        await update.message.reply_text("❌ Please enter a number", reply_markup=back_keyboard("back_add"))
        return ADD_COURSE_SEMESTER


async def add_course_professor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle course professor input."""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        
        if query.data == "back_add":
            return await back_to_add_menu(update, context)
        
        if query.data == "skip":
            context.user_data["course_professor"] = ""
            await query.edit_message_text("🎓 How many ECTS credits?", reply_markup=skip_keyboard())
            return ADD_COURSE_ECTS
    else:
        context.user_data["course_professor"] = update.message.text
        await update.message.reply_text("🎓 How many ECTS credits?", reply_markup=skip_keyboard())
        return ADD_COURSE_ECTS


async def add_course_ects(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle course ECTS and save to Notion."""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        
        if query.data == "back_add":
            return await back_to_add_menu(update, context)
        
        if query.data == "skip":
            ects = 0
        else:
            return ADD_COURSE_ECTS
    else:
        try:
            ects = int(update.message.text)
        except ValueError:
            await update.message.reply_text("❌ Please enter a number", reply_markup=skip_keyboard())
            return ADD_COURSE_ECTS
    
    result = notion_service.add_course(
        name=context.user_data["course_name"],
        course_code=context.user_data["course_code"],
        semester=context.user_data["course_semester"],
        professor=context.user_data.get("course_professor", ""),
        ects=ects
    )
    
    if result["success"]:
        response = (
            f"✅ Course added!\n\n"
            f"📖 {context.user_data['course_name']}\n"
            f"🔤 {context.user_data['course_code']}\n"
            f"📅 Semester {context.user_data['course_semester']}\n"
            f"👨‍🏫 {context.user_data.get('course_professor', 'N/A')}\n"
            f"🎓 {ects} ECTS"
        )
    else:
        response = f"❌ Error: {result['message']}"
    
    context.user_data.clear()
    
    if update.callback_query:
        await update.callback_query.edit_message_text(response, reply_markup=done_keyboard())
    else:
        await update.message.reply_text(response, reply_markup=done_keyboard())
    
    return MAIN_MENU


# =============================================================================
# LIST HANDLERS
# =============================================================================

async def list_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle list menu selections."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "back_main":
        return await start(update, context)
    
    if query.data == "list_assignments":
        items = notion_service.list_assignments()
        if not items:
            await query.edit_message_text("📭 No assignments found.", reply_markup=list_menu_keyboard())
            return LIST_MENU
        
        items = [i for i in items if i.get('name') and i['name'] != "Untitled"]
        
        if not items:
            await query.edit_message_text("📭 No assignments found.", reply_markup=list_menu_keyboard())
            return LIST_MENU
        
        await query.edit_message_text(
            "📝 Your Assignments:\n\nTap one to change its status:",
            reply_markup=items_list_keyboard(items, "assignment")
        )
        return LIST_ASSIGNMENTS_SELECT
    
    elif query.data == "list_labs":
        items = notion_service.list_labs()
        if not items:
            await query.edit_message_text("📭 No labs found.", reply_markup=list_menu_keyboard())
            return LIST_MENU
        
        items = [i for i in items if i.get('name') and i['name'] != "Untitled"]
        
        if not items:
            await query.edit_message_text("📭 No labs found.", reply_markup=list_menu_keyboard())
            return LIST_MENU
        
        await query.edit_message_text(
            "🔬 Your Labs:\n\nTap one to change its status:",
            reply_markup=items_list_keyboard(items, "lab")
        )
        return LIST_LABS_SELECT
    
    elif query.data == "list_projects":
        items = notion_service.list_projects()
        if not items:
            await query.edit_message_text("📭 No projects found.", reply_markup=list_menu_keyboard())
            return LIST_MENU
        
        items = [i for i in items if i.get('name') and i['name'] != "Untitled"]
        
        if not items:
            await query.edit_message_text("📭 No projects found.", reply_markup=list_menu_keyboard())
            return LIST_MENU
        
        await query.edit_message_text(
            "🎯 Your Projects:\n\nTap one to change its status:",
            reply_markup=items_list_keyboard(items, "project")
        )
        return LIST_PROJECTS_SELECT
    
    elif query.data == "list_courses":
        items = notion_service.list_courses()
        if not items:
            text = "📭 No courses found."
        else:
            items = [i for i in items if i.get('name') and i['name'] != "Untitled"]
            text = "📖 Your Courses:\n\n"
            for item in items:
                text += f"📚 {item['name']} ({item['course_code']})\n"
                text += f"   Semester {item['semester']} | {item['ects']} ECTS\n\n"
        
        await query.edit_message_text(text, reply_markup=list_menu_keyboard())
        return LIST_MENU
    
    return LIST_MENU


async def list_assignments_select_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle assignment selection for status update."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "back_list":
        await query.edit_message_text("What would you like to see?", reply_markup=list_menu_keyboard())
        return LIST_MENU
    
    if query.data.startswith("assignment_"):
        item_id = query.data.replace("assignment_", "")
        
        items = notion_service.list_assignments()
        item = None
        for i in items:
            if i['id'].startswith(item_id):
                item = i
                context.user_data["selected_item_id"] = i['id']
                context.user_data["selected_item_type"] = "assignment"
                break
        
        if item:
            emoji = _status_emoji(item['status'])
            text = (
                f"📝 *{item['name']}*\n\n"
                f"📚 Course: {item['course_code']}\n"
                f"📅 Due: {item['due_date']}\n"
                f"📌 Notes: {item['notes'] if item['notes'] else 'None'}\n"
                f"Status: {emoji} {item['status']}\n\n"
                f"What would you like to do?"
            )
            await query.edit_message_text(
                text,
                reply_markup=item_action_keyboard(item_id, "assignment"),
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text("❌ Item not found", reply_markup=list_menu_keyboard())
        
        return ITEM_ACTION
    
    return LIST_ASSIGNMENTS_SELECT


async def list_labs_select_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle lab selection for status update."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "back_list":
        await query.edit_message_text("What would you like to see?", reply_markup=list_menu_keyboard())
        return LIST_MENU
    
    if query.data.startswith("lab_"):
        item_id = query.data.replace("lab_", "")
        
        items = notion_service.list_labs()
        item = None
        for i in items:
            if i['id'].startswith(item_id):
                item = i
                context.user_data["selected_item_id"] = i['id']
                context.user_data["selected_item_type"] = "lab"
                break
        
        if item:
            emoji = _status_emoji(item['status'])
            text = (
                f"🔬 *{item['name']}*\n\n"
                f"📚 Course: {item['course_code']}\n"
                f"📅 Due: {item['due_date']}\n"
                f"📌 Notes: {item['notes'] if item['notes'] else 'None'}\n"
                f"Status: {emoji} {item['status']}\n\n"
                f"What would you like to do?"
            )
            await query.edit_message_text(
                text,
                reply_markup=item_action_keyboard(item_id, "lab"),
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text("❌ Item not found", reply_markup=list_menu_keyboard())
        
        return ITEM_ACTION
    
    return LIST_LABS_SELECT


async def list_projects_select_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle project selection for status update."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "back_list":
        await query.edit_message_text("What would you like to see?", reply_markup=list_menu_keyboard())
        return LIST_MENU
    
    if query.data.startswith("project_"):
        item_id = query.data.replace("project_", "")
        
        items = notion_service.list_projects()
        item = None
        for i in items:
            if i['id'].startswith(item_id):
                item = i
                context.user_data["selected_item_id"] = i['id']
                context.user_data["selected_item_type"] = "project"
                break
        
        if item:
            emoji = _status_emoji(item['status'])
            text = (
                f"🎯 *{item['name']}*\n\n"
                f"📚 Course: {item['course_code']}\n"
                f"📅 Due: {item['due_date']}\n"
                f"📌 Notes: {item['notes'] if item['notes'] else 'None'}\n"
                f"Status: {emoji} {item['status']}\n\n"
                f"What would you like to do?"
            )
            await query.edit_message_text(
                text,
                reply_markup=item_action_keyboard(item_id, "project"),
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text("❌ Item not found", reply_markup=list_menu_keyboard())
        
        return ITEM_ACTION
    
    return LIST_PROJECTS_SELECT


async def item_action_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle item actions (status, edit, delete)."""
    query = update.callback_query
    await query.answer()
    
    item_id = context.user_data.get("selected_item_id", "")
    item_type = context.user_data.get("selected_item_type", "")
    
    # Handle back buttons
    if query.data == "back_assignments":
        items = notion_service.list_assignments()
        items = [i for i in items if i.get('name') and i['name'] != "Untitled"]
        await query.edit_message_text(
            "📝 Your Assignments:\n\nTap one to change its status:",
            reply_markup=items_list_keyboard(items, "assignment")
        )
        return LIST_ASSIGNMENTS_SELECT
    
    elif query.data == "back_labs":
        items = notion_service.list_labs()
        items = [i for i in items if i.get('name') and i['name'] != "Untitled"]
        await query.edit_message_text(
            "🔬 Your Labs:\n\nTap one to change its status:",
            reply_markup=items_list_keyboard(items, "lab")
        )
        return LIST_LABS_SELECT
    
    elif query.data == "back_projects":
        items = notion_service.list_projects()
        items = [i for i in items if i.get('name') and i['name'] != "Untitled"]
        await query.edit_message_text(
            "🎯 Your Projects:\n\nTap one to change its status:",
            reply_markup=items_list_keyboard(items, "project")
        )
        return LIST_PROJECTS_SELECT
    
    # Handle status update
    if query.data.startswith("status_"):
        parts = query.data.split("_", 3)
        if len(parts) >= 4:
            new_status = parts[3]
            
            result = notion_service.update_status(item_id, new_status)
            
            if result["success"]:
                emoji = _status_emoji(new_status)
                await query.edit_message_text(
                    f"✅ Status updated to {emoji} {new_status}!",
                    reply_markup=done_keyboard()
                )
            else:
                await query.edit_message_text(
                    f"❌ Error: {result['message']}",
                    reply_markup=done_keyboard()
                )
            
            context.user_data.clear()
            return MAIN_MENU
    
    # Handle edit due date
    if query.data.startswith("editdate_"):
        await query.edit_message_text(
            "📅 Select new due date:",
            reply_markup=date_keyboard()
        )
        return EDIT_DATE
    
    # Handle edit course
    if query.data.startswith("editcourse_"):
        await query.edit_message_text(
            "📚 Select new course:",
            reply_markup=courses_keyboard()
        )
        return EDIT_COURSE
    
    # Handle edit notes
    if query.data.startswith("editnotes_"):
        await query.edit_message_text(
            "✏️ Type new notes (or send empty message to clear):",
            reply_markup=back_keyboard("back_action")
        )
        return EDIT_NOTES
    
    # Handle delete
    if query.data.startswith("delete_"):
        await query.edit_message_text(
            "⚠️ Are you sure you want to delete this item?\n\nThis cannot be undone!",
            reply_markup=confirm_delete_keyboard(item_id, item_type)
        )
        return CONFIRM_DELETE
    
    return ITEM_ACTION


async def edit_date_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle due date edit."""
    query = update.callback_query
    item_id = context.user_data.get("selected_item_id", "")
    item_type = context.user_data.get("selected_item_type", "")
    
    if query:
        await query.answer()
        
        if query.data == "back_add":
            item = notion_service.get_item_by_id(item_id)
            if item:
                emoji = _status_emoji(item['status'])
                type_emoji = {"assignment": "📝", "lab": "🔬", "project": "🎯"}.get(item_type, "📝")
                text = (
                    f"{type_emoji} *{item['name']}*\n\n"
                    f"📚 Course: {item['course_code']}\n"
                    f"📅 Due: {item['due_date']}\n"
                    f"📌 Notes: {item['notes'] if item['notes'] else 'None'}\n"
                    f"Status: {emoji} {item['status']}\n\n"
                    f"What would you like to do?"
                )
                await query.edit_message_text(
                    text,
                    reply_markup=item_action_keyboard(item_id[:32], item_type),
                    parse_mode="Markdown"
                )
            return ITEM_ACTION
        
        if query.data == "date_custom":
            await query.edit_message_text(
                "📅 Enter the new due date (YYYY-MM-DD):",
                reply_markup=back_keyboard("back_add")
            )
            return EDIT_DATE
        
        if query.data.startswith("date_"):
            new_date = query.data.replace("date_", "")
            result = notion_service.update_due_date(item_id, new_date)
            
            if result["success"]:
                await query.edit_message_text(
                    f"✅ Due date updated to {new_date}!",
                    reply_markup=done_keyboard()
                )
            else:
                await query.edit_message_text(
                    f"❌ Error: {result['message']}",
                    reply_markup=done_keyboard()
                )
            
            context.user_data.clear()
            return MAIN_MENU
    
    return EDIT_DATE


async def edit_date_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle custom date text input for editing."""
    date_text = update.message.text.strip()
    item_id = context.user_data.get("selected_item_id", "")
    
    try:
        datetime.strptime(date_text, "%Y-%m-%d")
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid format. Use YYYY-MM-DD (e.g., 2025-12-20)",
            reply_markup=back_keyboard("back_add")
        )
        return EDIT_DATE
    
    result = notion_service.update_due_date(item_id, date_text)
    
    if result["success"]:
        await update.message.reply_text(
            f"✅ Due date updated to {date_text}!",
            reply_markup=done_keyboard()
        )
    else:
        await update.message.reply_text(
            f"❌ Error: {result['message']}",
            reply_markup=done_keyboard()
        )
    
    context.user_data.clear()
    return MAIN_MENU


async def edit_course_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle course edit."""
    query = update.callback_query
    await query.answer()
    
    item_id = context.user_data.get("selected_item_id", "")
    item_type = context.user_data.get("selected_item_type", "")
    
    if query.data == "back_add":
        item = notion_service.get_item_by_id(item_id)
        if item:
            emoji = _status_emoji(item['status'])
            type_emoji = {"assignment": "📝", "lab": "🔬", "project": "🎯"}.get(item_type, "📝")
            text = (
                f"{type_emoji} *{item['name']}*\n\n"
                f"📚 Course: {item['course_code']}\n"
                f"📅 Due: {item['due_date']}\n"
                f"📌 Notes: {item['notes'] if item['notes'] else 'None'}\n"
                f"Status: {emoji} {item['status']}\n\n"
                f"What would you like to do?"
            )
            await query.edit_message_text(
                text,
                reply_markup=item_action_keyboard(item_id[:32], item_type),
                parse_mode="Markdown"
            )
        return ITEM_ACTION
    
    if query.data.startswith("course_"):
        new_course = query.data.replace("course_", "")
        result = notion_service.update_course(item_id, new_course)
        
        if result["success"]:
            await query.edit_message_text(
                f"✅ Course updated to {new_course}!",
                reply_markup=done_keyboard()
            )
        else:
            await query.edit_message_text(
                f"❌ Error: {result['message']}",
                reply_markup=done_keyboard()
            )
        
        context.user_data.clear()
        return MAIN_MENU
    
    return EDIT_COURSE


async def edit_notes_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle notes edit."""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        
        if query.data == "back_action":
            item_id = context.user_data.get("selected_item_id", "")
            item_type = context.user_data.get("selected_item_type", "")
            item = notion_service.get_item_by_id(item_id)
            if item:
                emoji = _status_emoji(item['status'])
                type_emoji = {"assignment": "📝", "lab": "🔬", "project": "🎯"}.get(item_type, "📝")
                text = (
                    f"{type_emoji} *{item['name']}*\n\n"
                    f"📚 Course: {item['course_code']}\n"
                    f"📅 Due: {item['due_date']}\n"
                    f"📌 Notes: {item['notes'] if item['notes'] else 'None'}\n"
                    f"Status: {emoji} {item['status']}\n\n"
                    f"What would you like to do?"
                )
                await query.edit_message_text(
                    text,
                    reply_markup=item_action_keyboard(item_id[:32], item_type),
                    parse_mode="Markdown"
                )
            return ITEM_ACTION
        
        return EDIT_NOTES
    
    new_notes = update.message.text.strip()
    item_id = context.user_data.get("selected_item_id", "")
    
    result = notion_service.update_notes(item_id, new_notes)
    
    if result["success"]:
        await update.message.reply_text(
            f"✅ Notes updated!",
            reply_markup=done_keyboard()
        )
    else:
        await update.message.reply_text(
            f"❌ Error: {result['message']}",
            reply_markup=done_keyboard()
        )
    
    context.user_data.clear()
    return MAIN_MENU


async def confirm_delete_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle delete confirmation."""
    query = update.callback_query
    await query.answer()
    
    item_id = context.user_data.get("selected_item_id", "")
    item_type = context.user_data.get("selected_item_type", "")
    
    if query.data.startswith("confirmdelete_"):
        result = notion_service.delete_item(item_id)
        
        if result["success"]:
            await query.edit_message_text(
                "✅ Item deleted!",
                reply_markup=done_keyboard()
            )
        else:
            await query.edit_message_text(
                f"❌ Error: {result['message']}",
                reply_markup=done_keyboard()
            )
        
        context.user_data.clear()
        return MAIN_MENU
    
    if query.data.startswith("canceldelete_"):
        item = notion_service.get_item_by_id(item_id)
        if item:
            emoji = _status_emoji(item['status'])
            type_emoji = {"assignment": "📝", "lab": "🔬", "project": "🎯"}.get(item_type, "📝")
            text = (
                f"{type_emoji} *{item['name']}*\n\n"
                f"📚 Course: {item['course_code']}\n"
                f"📅 Due: {item['due_date']}\n"
                f"📌 Notes: {item['notes'] if item['notes'] else 'None'}\n"
                f"Status: {emoji} {item['status']}\n\n"
                f"What would you like to do?"
            )
            await query.edit_message_text(
                text,
                reply_markup=item_action_keyboard(item_id[:32], item_type),
                parse_mode="Markdown"
            )
        return ITEM_ACTION
    
    return CONFIRM_DELETE


# =============================================================================
# UPCOMING HANDLERS
# =============================================================================

async def upcoming_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle upcoming menu selections."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "back_main":
        return await start(update, context)
    
    days = int(query.data.replace("upcoming_", ""))
    work = notion_service.get_upcoming(days)
    
    total = len(work["assignments"]) + len(work["labs"]) + len(work["projects"])
    
    if total == 0:
        text = f"🎉 Nothing due in the next {days} days!"
    else:
        text = f"📅 Due in the next {days} days:\n\n"
        
        if work["assignments"]:
            text += "📝 Assignments:\n"
            for a in work["assignments"]:
                text += f"  • {a['name']} ({a['course_code']}) - {a['due_date']}\n"
            text += "\n"
        
        if work["labs"]:
            text += "🔬 Labs:\n"
            for lab in work["labs"]:
                text += f"  • {lab['name']} ({lab['course_code']}) - {lab['due_date']}\n"
            text += "\n"
        
        if work["projects"]:
            text += "🎯 Projects:\n"
            for p in work["projects"]:
                text += f"  • {p['name']} ({p['course_code']}) - {p['due_date']}\n"
    
    await query.edit_message_text(text, reply_markup=upcoming_menu_keyboard())
    return UPCOMING_MENU


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current operation and return to main menu."""
    context.user_data.clear()
    await update.message.reply_text("❌ Cancelled. Returning to main menu.", reply_markup=main_menu_keyboard())
    return MAIN_MENU


# =============================================================================
# MAIN - WEBHOOK MODE FOR RENDER
# =============================================================================

def main():
    """Start the bot using webhooks (for Render deployment)."""
    # Validate config
    try:
        config.validate_config()
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return
    
    # Test Notion connection
    if not notion_service.test_connection():
        print("❌ Cannot connect to Notion.")
        return
    
    # Create application
    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    
    # Build conversation handler
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("menu", start),
        ],
        states={
            MAIN_MENU: [
                CallbackQueryHandler(main_menu_handler),
            ],
            ADD_MENU: [
                CallbackQueryHandler(add_menu_handler),
            ],
            
            # Assignment flow
            ADD_ASSIGNMENT_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_assignment_name),
                CallbackQueryHandler(back_to_add_menu, pattern="^back_add$"),
            ],
            ADD_ASSIGNMENT_COURSE: [
                CallbackQueryHandler(add_assignment_course),
            ],
            ADD_ASSIGNMENT_DATE: [
                CallbackQueryHandler(add_assignment_date),
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_assignment_date_text),
            ],
            ADD_ASSIGNMENT_NOTES: [
                CallbackQueryHandler(add_assignment_notes),
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_assignment_notes),
            ],
            
            # Lab flow
            ADD_LAB_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_lab_name),
                CallbackQueryHandler(back_to_add_menu, pattern="^back_add$"),
            ],
            ADD_LAB_COURSE: [
                CallbackQueryHandler(add_lab_course),
            ],
            ADD_LAB_DATE: [
                CallbackQueryHandler(add_lab_date),
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_lab_date_text),
            ],
            ADD_LAB_DESCRIPTION: [
                CallbackQueryHandler(add_lab_description),
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_lab_description),
            ],
            ADD_LAB_NOTES: [
                CallbackQueryHandler(add_lab_notes),
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_lab_notes),
            ],
            
            # Project flow
            ADD_PROJECT_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_project_name),
                CallbackQueryHandler(back_to_add_menu, pattern="^back_add$"),
            ],
            ADD_PROJECT_COURSE: [
                CallbackQueryHandler(add_project_course),
            ],
            ADD_PROJECT_DATE: [
                CallbackQueryHandler(add_project_date),
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_project_date_text),
            ],
            ADD_PROJECT_NOTES: [
                CallbackQueryHandler(add_project_notes),
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_project_notes),
            ],
            
            # Course flow
            ADD_COURSE_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_course_name),
                CallbackQueryHandler(back_to_add_menu, pattern="^back_add$"),
            ],
            ADD_COURSE_CODE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_course_code),
                CallbackQueryHandler(back_to_add_menu, pattern="^back_add$"),
            ],
            ADD_COURSE_SEMESTER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_course_semester),
                CallbackQueryHandler(back_to_add_menu, pattern="^back_add$"),
            ],
            ADD_COURSE_PROFESSOR: [
                CallbackQueryHandler(add_course_professor),
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_course_professor),
            ],
            ADD_COURSE_ECTS: [
                CallbackQueryHandler(add_course_ects),
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_course_ects),
            ],
            
            # List menu
            LIST_MENU: [
                CallbackQueryHandler(list_menu_handler),
            ],
            LIST_ASSIGNMENTS_SELECT: [
                CallbackQueryHandler(list_assignments_select_handler),
            ],
            LIST_LABS_SELECT: [
                CallbackQueryHandler(list_labs_select_handler),
            ],
            LIST_PROJECTS_SELECT: [
                CallbackQueryHandler(list_projects_select_handler),
            ],
            ITEM_ACTION: [
                CallbackQueryHandler(item_action_handler),
            ],
            EDIT_DATE: [
                CallbackQueryHandler(edit_date_handler),
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_date_text_handler),
            ],
            EDIT_COURSE: [
                CallbackQueryHandler(edit_course_handler),
            ],
            EDIT_NOTES: [
                CallbackQueryHandler(edit_notes_handler),
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_notes_handler),
            ],
            CONFIRM_DELETE: [
                CallbackQueryHandler(confirm_delete_handler),
            ],
            
            # Upcoming menu
            UPCOMING_MENU: [
                CallbackQueryHandler(upcoming_menu_handler),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("start", start),
        ],
    )
    
    app.add_handler(conv_handler)
    
    # --- WEBHOOK MODE ---
    # Render sets RENDER_EXTERNAL_URL automatically for web services
    webhook_url = config.RENDER_EXTERNAL_URL
    port = config.PORT
    
    if webhook_url:
        # Running on Render — use webhooks
        print(f"🚀 Bot starting in WEBHOOK mode on port {port}")
        print(f"🔗 Webhook URL: {webhook_url}")
        app.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path="webhook",
            webhook_url=f"{webhook_url}/webhook",
        )
    else:
        # Running locally — use polling (for development)
        print("🚀 Bot starting in POLLING mode (local development)")
        app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()