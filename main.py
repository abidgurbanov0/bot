bot_token = '6773122549:AAEYjRn2mNa6SCJidZeAyx6lFrwxrr8fJLI'
from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, CallbackContext
from telegram.utils.helpers import escape_markdown
import requests
from datetime import datetime
import psycopg2
from telegram import InputMediaPhoto
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters

# Database connection parameters
host = "connectify-db.postgres.database.azure.com"
database_name = "connectify"
user = "connectifyadmin"
password = "Eden258eden"
table_name = "events"
selected_event_type = None  # New global variable to store selected event type

def start(update: Update, context: CallbackContext) -> None:
    # Get the user's first name
    user_name = update.message.from_user.first_name

    # Send a welcome message
    update.message.reply_text(f"Hello {user_name}! Welcome to your Connectify bot. If you wish to look at all events write /getall else /selectcategory")

# Function to handle the /getall command
def get_all_events(update: Update, context: CallbackContext) -> None:
    # Connection to the PostgreSQL database
    connection = psycopg2.connect(
        host=host,
        user=user,
        password=password,
        dbname=database_name,
        port=5432,
        sslmode="require"  # or "disable" if SSL is not required
    )

    # Create a cursor object to execute SQL queries
    cursor = connection.cursor()

    # Query to select all data from the "events" table
    query = f"SELECT * FROM {table_name};"

    # Execute the query
    cursor.execute(query)

    # Fetch all rows from the result set
    rows = cursor.fetchall()

    # Close the cursor and connection
    cursor.close()
    connection.close()

    # Loop through each row and send event information
    for row in rows:
        event_dict = {
            "eventTitle": row[12],
            "eventStatus": row[11],
            "eventTypes": row[15],
            "eventStartDate": row[10],
            "eventEndDate": row[9],
            "eventVenueAddress": row[13],
            "eventDescription": row[8],
            "estimatedCrowdSize": row[7],
            "cashSponsorshipNeeded": row[2],
            "committeeSize": row[3],
            "contactPersonName": row[5],
            "contactPersonEmail": row[4],
            "contactPersonPhoneNumber": row[6],
            "image": row[14],
            "clubName": row[1]  # Assuming club name is the same as event title
        }

        # Format the event dictionary as a string
        event_str = "\n".join([f"{key}: {value}" for key, value in event_dict.items()])

        # Send the event text as a message with better formatting
        update.message.reply_text(f"Event:\n\n{event_str}\n")

def special_event_type(update: Update, context: CallbackContext) -> None:
    event_types_response = requests.get("http://54.81.172.39/api/v1/organizer/event-types")

    try:
        event_types = event_types_response.json()
    except ValueError:
        update.message.reply_text("Error fetching event types. Please try again later.")
        return

    # Create a keyboard with event types for user selection
    keyboard = [[event_type] for event_type in event_types]

    update.message.reply_text(
        "Choose a special event type:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    )

# Function to handle the user's selection of an event type
def handle_event_type_selection(update: Update, context: CallbackContext) -> None:
    global selected_event_type
    selected_event_type = update.message.text.lower()
    update.message.reply_text(f"Selected event type: {selected_event_type} Now /getselectedevents to get events")

def get_selected_events(update: Update, context: CallbackContext) -> None:
    global selected_event_type

    # Check if an event type is selected
    if selected_event_type:
        # Connection to the PostgreSQL database
        connection = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            dbname=database_name,
            port=5432,
            sslmode="require"  # or "disable" if SSL is not required
        )

        # Create a cursor object to execute SQL queries
        cursor = connection.cursor()

        # Query to select events based on the selected event type
        query = f"SELECT * FROM {table_name} WHERE LOWER(event_type) LIKE LOWER('%{selected_event_type.casefold()}%');"

        # Execute the query
        cursor.execute(query)

        # Fetch all rows from the result set
        rows = cursor.fetchall()

        # Close the cursor and connection
        cursor.close()
        connection.close()

        # Loop through each row and send event information
        for row in rows:
            event_dict = {
                "eventTitle": row[12],
                "eventStatus": row[11],
                "eventTypes": row[15],
                "eventStartDate": row[10],
                "eventEndDate": row[9],
                "eventVenueAddress": row[13],
                "eventDescription": row[8],
                "estimatedCrowdSize": row[7],
                "cashSponsorshipNeeded": row[2],
                "committeeSize": row[3],
                "contactPersonName": row[5],
                "contactPersonEmail": row[4],
                "contactPersonPhoneNumber": row[6],
                "image": row[14],
                "clubName": row[1]  # Assuming club name is the same as event title
            }

            # Format the event dictionary as a string
            event_str = "\n".join([f"{key}: {value}" for key, value in event_dict.items()])

            # Send the event text as a message with better formatting
            update.message.reply_text(f"Event:\n\n{event_str}\n")
    else:
        update.message.reply_text("No event type selected. Use /selectcategory command to choose an event type.")

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

# Start the Bot
updater.start_polling()

# Run the bot until you send a signal to stop it
updater.idle()
