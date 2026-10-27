import json
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from openai import AuthenticationError, OpenAI

ROOT = Path(__file__).resolve().parent
HISTORY_PATH = ROOT / "chat_history.json"

# Load this project's .env even if a stale OPENAI_API_KEY is already set in Windows.
load_dotenv(ROOT / ".env", override=True)

# Edit this text to change how the bot behaves. No other cricket notes are loaded.
SYSTEM_PROMPT = """
You are Cricket adda, a friendly cricket expert.

You know the laws of cricket, formats (Test, ODI, T20, and others), tactics, fielding positions, gear, tournaments, history, and players.

Follow these rules on every reply:
1. Talk about cricket only.
2. If a question is not about cricket but you can honestly connect it to cricket, answer through that cricket link. Example: a question about the weather becomes an answer about the pitch, swing, and match conditions.
3. If you cannot connect the question to cricket, reply with exactly this text and nothing else: out of the context
4. Language: reply in English. If the user writes in Tinglish (Telugu mixed with English, written in English letters), reply in Tinglish.
5. Length: keep a short answer short. If the answer would be long, start with one short summary line, then use bullet points. Do not write long paragraphs.
6. Do not invent live scores. If you are unsure of a fact or statistic, say you are not sure.
""".strip()


def save_history(messages):
    """Overwrite the JSON file with the current chat only."""
    HISTORY_PATH.write_text(json.dumps(messages, indent=2), encoding="utf-8")


def ask_cricket_adda(messages):
    client = OpenAI(api_key=(os.getenv("OPENAI_API_KEY") or "").strip())
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, *messages],
    )
    return response.choices[0].message.content or "out of the context"


st.set_page_config(page_title="Cricket adda", page_icon="🏏")
st.title("Cricket adda")
st.caption("Cricket only. Ask about rules, players, tactics, or matches.")

if not os.getenv("OPENAI_API_KEY"):
    st.error("Add your OpenAI key to the .env file as OPENAI_API_KEY, then restart the app.")
    st.stop()

# A new visit starts with an empty chat. Old messages in the JSON file are not loaded.
if "messages" not in st.session_state:
    st.session_state.messages = []
    save_history([])

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Ask a cricket question")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    save_history(st.session_state.messages)

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            reply = ask_cricket_adda(st.session_state.messages)
        except AuthenticationError:
            reply = "OpenAI rejected the API key. Put a valid OPENAI_API_KEY in .env, then restart the app."
        except Exception as exc:
            # Do not show the raw error in the UI. It can include part of the API key.
            print(exc)
            reply = "Could not reach OpenAI. Check your internet connection and try again."
        
    st.session_state.messages.append({"role": "assistant", "content": reply})
    save_history(st.session_state.messages)
    st.markdown(reply)