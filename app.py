import os
from pathlib import Path
from dotenv import load_dotenv
import boto3
import json
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import logging
from datetime import datetime

#Log 
logging.basicConfig(
    filename='logfile.log',  # Log file name
    level=logging.INFO,  # Log level
    format='%(message)s',  # Only include the log message (no additional info)
)

def log_entry(user):
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    log_message = f"Logged in at [{current_time}] by {user}"
    
    # Log the message
    logging.info(log_message)
    
    #file write
    with open('logfile.txt', 'a') as log_file:
        log_file.write(log_message)

#logging end




# Load environment variables from .env file
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# Get environment variables for Slack tokens
slack_bot_token = os.environ.get("SLACK_BOT_TOKEN")
slack_app_token = os.environ.get("SLACK_APP_TOKEN")

# Initialize the Slack app
app = App(token=slack_bot_token)

# Function to invoke Lambda
def invoke_lambda(function_name, payload):
    client = boto3.client('lambda', region_name='us-east-1')

    try:
        response = client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )

        # Log the response from Lambda
        response_payload = response['Payload'].read().decode('utf-8')
        print("Lambda response:", response_payload)

    except Exception as e:
        print(f"Error invoking Lambda function: {e}")

# Slack command handler
@app.command("/help")
def handle_snowflake_command(ack, body, client):
    # Acknowledge the command immediately
    ack()
    
    try:
        # Get user info
        user_info = client.users_info(user=body["user_id"])
        user_name = user_info["user"]["real_name"]
        
        print("--------", user_name,"-------------")
        #logging for entry
        log_entry(user_name)

        # Construct modal view
        view = {
            "type": "modal",
            "callback_id": "snowflake_query_modal",
            "title": {"type": "plain_text", "text": "Snowflake Query"},
            "submit": {"type": "plain_text", "text": "Run Query"},
            "blocks": [
                {
                    "type": "input",
                    "block_id": "query_block",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "snowflake_query",
                        "multiline": True,
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Enter your Snowflake SQL query here..."
                        }
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "Query",
                        "emoji": True
                    }
                }
            ]
        }

        # Open modal
        client.views_open(
            trigger_id=body["trigger_id"],
            view=view
        )

    except Exception as e:
        client.chat_postMessage(
            channel=body["channel_id"],
            text=f"Error: {str(e)}"
        )

@app.view("snowflake_query_modal")
def handle_query_submission(ack, body, client, view):
    # Acknowledge the view submission
    ack()
    
    try:
        # Extract query from the submission
        query = view["state"]["values"]["query_block"]["snowflake_query"]["value"]
        user_id = body["user"]["id"]
        
        # Get user info
        user_info = client.users_info(user=user_id)
        user_name = user_info["user"]["real_name"]

        # Prepare payload for Lambda
        lambda_function_name = "snowflake_connection"
        event_payload = {
            "query": query
        }
        
        # Invoke Lambda
        #invoke_lambda(lambda_function_name, event_payload)

        # Send confirmation message
        client.chat_postMessage(
            channel=user_id,  # Send DM to user
            text="Your query is being processed. Results will be sent here shortly."
        )

    except Exception as e:
        client.chat_postMessage(
            channel=user_id,
            text=f"Error processing your query: {str(e)}"
        )

# Error handler
@app.error
def custom_error_handler(error, body, client):
    client.chat_postMessage(
        channel=body["container"]["channel_id"],
        text=f"An error occurred: {str(error)}"
    )
# Run the Slack app
if __name__ == "__main__":
    handler = SocketModeHandler(app, slack_app_token)
    handler.start()
