from twilio.rest import Client
import os

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_number = os.getenv("TWILIO_PHONE_NUMBER")


client = Client(account_sid, auth_token)
def inform_police_stations(criminal_name, location = 'texas'):
    message = client.messages.create(
        body=f"🚨 CrimeSight Alert: {criminal_name} spotted at {location}.",
        from_="+1234567890",
        to="+1987654321"  # police contact
    )
