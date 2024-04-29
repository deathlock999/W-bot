import os
import time
import requests
import gspread
from flask import Flask  # Fixed typo here
from deep_translator import GoogleTranslator

api_token = "fGQJvjbzsCUPB7QtImHL8okh7QEPnpzm"
url = "https://gate.whapi.cloud/messages/poll"
group_id = "120363261013619385@g.us"
sheet_id = "1ddIhjrBUJaA7Rc0oZTzc4wf1Tn6_ABn-fB8GTZD4YNQ"
worksheet_name = "Sheet1"

def update_index_file():
    try:
        with open("file.txt", 'r+') as f:
            # Handle empty file case (initialize to 0)
            content = f.read()
            last_index_id = int(content.strip()) if content else 0
            # Increment and update the file
            last_index_id += 1
            f.seek(0)
            f.write(str(last_index_id))
            # Return the updated last index ID
            return last_index_id
    except FileNotFoundError:
        # Handle case where the file doesn't exist (create it with initial value 0)
        with open("file.txt", 'w') as f:
            f.write('0')
            return 0

def translate(to_translate):
    translated = GoogleTranslator(source='auto', target='si').translate(to_translate)
    return translated

# Function to get data from Google Sheets
def get_data_from_sheets(sheet_id, worksheet_name, last_question_index, source_language='en', target_language='si'):
    try:
        gc = gspread.service_account(filename="luca-420106-ab9a1b42fc61.json")
        worksheet = gc.open_by_key(sheet_id).worksheet(worksheet_name)
        question = worksheet.cell(last_question_index, 1).value
        if not question:
            print(f"Empty row encountered at index {last_question_index}. Skipping...")
            return None
        answers = []
        all_answers_filled = True
        for i in range(2, 6):
            if (len(answers) < 4):
                answer = worksheet.cell(last_question_index, i).value
                if answer:
                    answers.append(answer)
                else:
                    all_answers_filled = False
                    break
        if not all_answers_filled:
            print(f"Row {last_question_index} skipped due to empty answer(s).")
            return None
        correct_answer = worksheet.cell(last_question_index, 6).value
        translator = GoogleTranslator(source=source_language, target=target_language)
        translated_question = translator.translate(question)
        translated_answers = [translator.translate(answer) for answer in answers]
        translated_correct_answer = translator.translate(correct_answer)
        return {
            "question": translated_question,
            "answers": translated_answers,
            "correct_answer": translated_correct_answer
        }
    except Exception as e:
        print(f"Error retrieving data from Google Sheet: {e}")
        return None 

# Function to send a poll to WhatsApp group
def send_poll(question, answers):
    payload = {
        "to": group_id,
        "options": answers,
        "title": question,
        "count": 1,
        "ephemeral": 10
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": api_token
    }
    response = requests.post(url, json=payload, headers=headers)
    print(response.text)

# Function to send a message with correct answer to WhatsApp group
def send_message(api_token, group_id, correct_answer):
    base_url = "https://gate.whapi.cloud/"
    endpoint = "messages/text"
    message = f"**Correct answer**\n \n✅ {correct_answer}"
    headers = {
        "Authorization": f"Bearer {api_token}"
    }
    data = {
        "to": group_id,
        "body": message
    }
    try:
        response = requests.post(url=f"{base_url}{endpoint}", headers=headers, json=data)
        response.raise_for_status()
        return response.json()
        print("Sent")
    except requests.exceptions.RequestException as error:
        print(f"Error sending message: {error}")
        return None

app = Flask(__name__)

@app.route('/')
def index():
    while True:
        last_question_index = update_index_file()
        print(last_question_index)
        data = get_data_from_sheets(sheet_id, worksheet_name, last_question_index)
        if data:
            question = data["question"]
            answers = data["answers"]
            correct_answer = data["correct_answer"]
            send_poll(question, answers)
            answers.clear()
            time.sleep(1800) 
            send_message(api_token, group_id, correct_answer)              
            time.sleep(1800)     
            print("...one cycle...")
        return "Your Flask application is running!"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
