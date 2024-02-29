import os
import psycopg2
import random
from datetime import date

from twilio.rest import Client

database_url = os.environ['DATABASE_URL']

def get_people_to_call():
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT name, last_called, interval
            FROM people
        """)
        people = cursor.fetchall()

        to_call = []
        for name, last_called, interval in people:
            if (date.today() - last_called).days >= interval:
                to_call.append(name)

        return to_call

    except Exception as e:
        print("Error:", e)
    finally:
        cursor.close()
        conn.close()

def send_text(body):
    account_sid = os.environ['ACCOUNT_SID']
    auth_token = os.environ['AUTH_TOKEN']

    twilio_number = os.environ['TWILIO_NUMBER']
    recipient_number = os.environ['RECIPIENT_NUMBER']

    client = Client(account_sid, auth_token)

    client.messages.create(
        body=body,
        from_=twilio_number,
        to=recipient_number,
    )

def main():
    people_to_call = get_people_to_call()

    if people_to_call:
        name = random.choice(people_to_call)
        body = f"Have you called {name} lately?"
        
        send_text(body)

        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE people
            SET last_called = %s
            WHERE name = %s
        """, (date.today(), name))
        conn.commit()
        conn.close()

if __name__ == "__main__":
    main()


