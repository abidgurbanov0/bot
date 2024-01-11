# Import necessary modules
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters
from telegram.utils.helpers import escape_markdown
import requests
from datetime import datetime
import psycopg2
import os
from decouple import config  # Import the config function from python-decouple

# Database connection parameters
table_name = "events"
selected_event_type = None  # New global variable to store the selected event type

# Configure environment variables
bot_token = config('BOT_TOKEN')
DATABASE_URL = config('DATABASE_URL')

# Connection to the PostgreSQL database
connection = psycopg2.connect(DATABASE_URL, sslmode='require')

# Create a cursor object to execute SQL queries
cursor = connection.cursor()

# Function to handle the /start command
def start(update: Update, context: CallbackContext) -> None:
    user_name = update.message.from_user.first_name
    update.message.reply_text(f"Hello {user_name}! Welcome to your Connectify bot. If you wish to look at all events write /getall else /selectcategory")

# Function to handle the /getall command
def get_all_events(update: Update, context: CallbackContext) -> None:
    try:
        # Query to select all data from the "events" table
        query = f"SELECT * FROM {table_name};"

        # Execute the query
        cursor.execute(query)

        # Fetch all rows from the result set
        rows = cursor.fetchall()

        # Loop through each row and send event information
        for row in rows:
            event_dict = {
                "eventTitle": row[12],
                "eventStatus": row[11],
                "eventTypes": row[15],
                # Add other fields based on your database schema
            }

            # Format the event dictionary as a string
            event_str = "\n".join([f"{key}: {value}" for key, value in event_dict.items()])

            # Send the event text as a message with better formatting
            update.message.reply_text(f"Event:\n\n{event_str}\n")

    except Exception as e:
        update.message.reply_text(f"Error fetching events: {str(e)}")

# Function to handle the /selectcategory command
def special_event_type(update: Update, context: CallbackContext) -> None:
    try:
        event_types_response = requests.get("http://54.81.172.39/api/v1/organizer/event-types")
        event_types = event_types_response.json()

        # Create a keyboard with event types for user selection
        keyboard = [[event_type] for event_type in event_types]

        update.message.reply_text(
            "Choose a special event type:",
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        )

    except Exception as e:
        update.message.reply_text(f"Error fetching event types: {str(e)}")

# Function to handle the user's selection of an event type
def handle_event_type_selection(update: Update, context: CallbackContext) -> None:
    global selected_event_type
    selected_event_type = update.message.text.lower()
    update.message.reply_text(f"Selected event type: {selected_event_type} Now /getselectedevents to get events")

# Function to handle the /getselectedevents command
def get_selected_events(update: Update, context: CallbackContext) -> None:
    global selected_event_type

    try:
        # Query to select events based on the selected event type
        query = f"SELECT * FROM {table_name} WHERE LOWER(event_type) LIKE LOWER('%{selected_event_type.casefold()}%');"

        # Execute the query
        cursor.execute(query)

        # Fetch all rows from the result set
        rows = cursor.fetchall()

        # Loop through each row and send event information
        for row in rows:
            event_dict = {
                "eventTitle": row[12],
                "eventStatus": row[11],
                "eventTypes": row[15],
                # Add other fields based on your database schema
            }

            # Format the event dictionary as a string
            event_str = "\n".join([f"{key}: {value}" for key, value in event_dict.items()])

            # Send the event text as a message with better formatting
            update.message.reply_text(f"Event:\n\n{event_str}\n")

    except Exception as e:
        update.message.reply_text(f"Error fetching selected events: {str(e)}")

# Create the Updater and pass it your bot's token
updater = Updater(token=bot_token, use_context=True)

# Get the dispatcher to register handlers
dispatcher = updater.dispatcher

# Register command handlers
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("getall", get_all_events))
dispatcher.add_handler(CommandHandler("selectcategory", special_event_type))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_event_type_selection))
dispatcher.add_handler(CommandHandler("getselectedevents", get_selected_events))

# Define the stop_and_close function to ensure proper cleanup
def stop_and_close():
    cursor.close()
    connection.close()

# Run the bot until you send a signal to stop it
updater.start_polling()
updater.idle()

# Call the stop_and_close function to close the cursor and connection
stop_and_close()
