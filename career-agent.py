from dotenv import load_dotenv
import os
import json
from openai import OpenAI
from openai.types.beta.chatkit.chat_session_chatkit_configuration_param import History
import requests
from pypdf import PdfReader
import gradio as gr

from constant import record_unknown_question_json, record_user_details_json

load_dotenv(override=True)
pushover_user = os.getenv("PUSHOVER_USER")
pushover_token = os.getenv("PUSHOVER_TOKEN")
openai_api_key = os.getenv("OPENAI_API_KEY")

openai = OpenAI(api_key=openai_api_key)

def record_user_details(email, name="No Name provided", notes="No notes provided"):
    push_notification(f"New user details recorded: {email}, {name} and {notes}")
    return {"recorded": "ok"}

def record_unknown_question(question):
    push_notification(f"New unknown question recorded: {question}")
    return {"recorded": "ok"}

def push_notification(message):
    pushover_url = "https://api.pushover.net/1/messages.json"
    payload = {
        "user": pushover_user,
        "token": pushover_token,
        "message": message
    }
    print(payload)
    response = requests.post(pushover_url, data=payload)
    if response.status_code != 200:
        raise Exception(f"Failed to send push notification: {response.text}")

def handle_tool_calls(tool_calls):
    results = []
    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)
        tool = globals().get(tool_name)
        result = tool(**args) if tool else {}
        results.append({"role": "tool", "content": json.dumps(result), "tool_call_id": tool_call.id})
    return results

def get_system_prompt():
    name = "Saumya Bhatnagar"
    reader = PdfReader("me/linkedin.pdf")
    linkedin_text = ""
    for page in reader.pages:
        linkedin_text += page.extract_text()

    resume_text = ""
    reader = PdfReader("me/resume.pdf")
    for page in reader.pages:
        resume_text += page.extract_text()

    summary = ""
    with open("me/summary.txt", "r") as file:
        summary = file.read()

    system_prompt = f"You are acting as {name}. You are answering questions on {name}'s website, \
    particularly questions related to {name}'s career, background, skills and experience. \
    Your responsibility is to represent {name} for interactions on the website as faithfully as possible. \
    You are given a summary of {name}'s background and LinkedIn profile which you can use to answer questions. \
    Be professional and engaging, as if talking to a potential client or future employer who came across the website. \
    If you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer, even if it's about something trivial or unrelated to career. \
    If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email and record it using your record_user_details tool. "
    system_prompt += f"\n\n## Summary:\n{summary}\n\n## LinkedIn Profile:\n{linkedin_text}\n\n## Resume:\n{resume_text}\n\n"
    system_prompt += f"With this context, please chat with the user, always staying in character as {name}."
    return system_prompt

def chat(message, history):
    tools = [
        {
            "type": "function",
            "function": record_user_details_json
        },
        {
            "type": "function",
            "function": record_unknown_question_json
        }
    ]
    system_prompt = get_system_prompt()
    messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": message}]
    done = False
    while not done:
        response = openai.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=tools)
        finish_reason = response.choices[0].finish_reason
        if finish_reason == "tool_calls":
            message = response.choices[0].message
            tool_calls = message.tool_calls
            results = handle_tool_calls(tool_calls)
            messages.append(message)
            messages.extend(results)
        else:
            done = True
    return response.choices[0].message.content
            

def main():
    gr.ChatInterface(chat).launch()

if __name__ == "__main__":
    main()