import os
import requests
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ConversationHandler, filters, CallbackContext, CallbackQueryHandler
)

# Load environment variables
load_dotenv()

TOKEN = os.getenv('TOKEN')

# Conversation states
CLIENT_NAME, CONTACT, SESSION_TYPE, DATE, TIME, PEOPLE, BOOKED_BY, TOTAL_PRICE = range(8)

# Start command
async def start(update: Update, context: CallbackContext) -> int:
    # Retrieve the topic ID (chat_id) when the /start command is triggered
    topic_id = update.message.chat.id
    context.user_data['topic_id'] = topic_id  # Store topic ID

    await update.message.reply_text("Tos Book! What is the client name?")
    
    # Send the topic ID to Make.com webhook
    make_url = 'https://hook.us2.make.com/a8x90abvt3nijoi7gydmplwwt273ex8h'
    requests.post(make_url, json={"topic_id": topic_id})

    return CLIENT_NAME

# Handlers for each step
async def client_name(update: Update, context: CallbackContext) -> int:
    context.user_data['client_name'] = update.message.text
    await update.message.reply_text("Got it! What is the contact?")
    return CONTACT

async def contact(update: Update, context: CallbackContext) -> int:
    context.user_data['contact'] = update.message.text
    await update.message.reply_text("What type of session would you like to book?")
    return SESSION_TYPE

async def session_type(update: Update, context: CallbackContext) -> int:
    context.user_data['session_type'] = update.message.text
    await update.message.reply_text("Please provide the date of the session (dd/mm/yyyy).")
    return DATE

async def date(update: Update, context: CallbackContext) -> int:
    context.user_data['date'] = update.message.text
    await update.message.reply_text("What time would you like to book (HH:MM)?")
    return TIME

async def time(update: Update, context: CallbackContext) -> int:
    context.user_data['time'] = update.message.text
    await update.message.reply_text("How many people will be attending?")
    return PEOPLE

async def people(update: Update, context: CallbackContext) -> int:
    try:
        people = int(update.message.text)
        if people <= 0:
            raise ValueError
        context.user_data['people'] = people
        await update.message.reply_text("Who booked this session?")
        return BOOKED_BY
    except ValueError:
        await update.message.reply_text("Please enter a valid number of people.")
        return PEOPLE

async def booked_by(update: Update, context: CallbackContext) -> int:
    context.user_data['booked_by'] = update.message.text
    await update.message.reply_text("Finally, what's the total price for the session?")
    return TOTAL_PRICE

async def total_price(update: Update, context: CallbackContext) -> int:
    try:
        price = float(update.message.text)
        if price <= 0:
            raise ValueError
        context.user_data['total_price'] = price
        
        # Summary of the order with bold formatting and currency for total price
        summary = (
            f"**Booking Summary**\n"
            f"**Client Name**: {context.user_data['client_name']}\n"
            f"**Contact**: {context.user_data['contact']}\n"
            f"**Session Type**: {context.user_data['session_type']}\n"
            f"**Date**: {context.user_data['date']}\n"
            f"**Time**: {context.user_data['time']}\n"
            f"**Number of People**: {context.user_data['people']}\n"
            f"**Booked By**: {context.user_data['booked_by']}\n"
            f"**Total Price**: ${context.user_data['total_price']:.2f}\n"
        )

        # Inline button to send the receipt
        keyboard = [[InlineKeyboardButton("Send Receipt", callback_data="send_receipt")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send summary with the button
        await update.message.reply_text(summary, parse_mode='Markdown', reply_markup=reply_markup)
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Please enter a valid price.")
        return TOTAL_PRICE

# Callback handler when "Send Receipt" button is clicked
async def button_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "send_receipt":
        # Collect the summary data
        summary_data = {
            "topic_id": context.user_data['topic_id'],  # Include topic ID
            "client_name": context.user_data['client_name'],
            "contact": context.user_data['contact'],
            "session_type": context.user_data['session_type'],
            "date": context.user_data['date'],
            "time": context.user_data['time'],
            "people": context.user_data['people'],
            "booked_by": context.user_data['booked_by'],
            "total_price": context.user_data['total_price']
        }

        # Send the summary data to Make.com via webhook
        make_url = 'https://hook.us2.make.com/a8x90abvt3nijoi7gydmplwwt273ex8h'
        response = requests.post(make_url, json=summary_data)

        # Prepare the confirmation message with a link to a private channel
        confirmation_message = (
            "The receipt will be ready and sent to [https://t.me/+J3_D4Bh5Z0hiNzE1]."
        )

        # Edit the original message to include the confirmation
        await query.edit_message_text(text=f"{confirmation_message}\n\n{query.message.text}", parse_mode='Markdown', reply_markup=query.message.reply_markup)

# Cancel the order
async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Booking has been canceled. You can start a new one anytime with /start.")
    return ConversationHandler.END

# Restart the order
async def restart(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Let's restart your order. What is the client name?")
    return CLIENT_NAME

# Fallback handler for unrecognized input
async def fallback(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Nhe nhai mes! Use /start to begin or /cancel to stop.")
    return ConversationHandler.END

# Main function to initialize the bot
def main():
    application = Application.builder().token(TOKEN).build()

    # Define the conversation handler steps
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CLIENT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, client_name)],
            CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact)],
            SESSION_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, session_type)],
            DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, date)],
            TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, time)],
            PEOPLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, people)],
            BOOKED_BY: [MessageHandler(filters.TEXT & ~filters.COMMAND, booked_by)],
            TOTAL_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, total_price)]
        },
        fallbacks=[CommandHandler('cancel', cancel), CommandHandler('restart', restart)]
    )

    # Add handlers
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(button_callback))

    # Run the bot
    application.run_polling()

if __name__ == '__main__':
    main()