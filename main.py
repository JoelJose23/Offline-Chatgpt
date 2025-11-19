import requests
import json
import datetime
import os

MAX_MESSAGES = 20
CONV_DIR = "Iris/conversations"

if not os.path.exists(CONV_DIR):
    os.makedirs(CONV_DIR)

def fetch_data_from_model(prompt:str):
        """Stream response from LLaMA in real time (token-by-token)."""
        with requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.2-vision",
                "prompt": prompt,
                "stream": True,   # 👈 Enable streaming here
            },
            stream=True,          # 👈 Important: make requests stream instead of buffering
        ) as response:
            for line in response.iter_lines():
                if line:
                    try:
                        data = line.decode("utf-8")
                        if data.startswith("data: "):
                            data = data[6:]  # remove "data: "
                        if data.strip() == "[DONE]":
                            break
                        # Each chunk is JSON containing part of the response
                        json_data = json.loads(data)
                        if "response" in json_data:
                            yield json_data["response"]
                    except Exception as e:
                        print("Stream error:", e)


def new_conversation():
    # Ensure folder exists
    try:
        os.makedirs(CONV_DIR, exist_ok=True)
    except Exception as e:
        print("ERROR: cannot create conversations folder:", e)
        raise

    # List current files (only regular files)
    files = [
        os.path.join(CONV_DIR, f)
        for f in os.listdir(CONV_DIR)
        if os.path.isfile(os.path.join(CONV_DIR, f))
    ]

    # If over limit, delete oldest files so we'll have space for a new one
    if len(files) >= MAX_MESSAGES:
        files.sort(key=os.path.getmtime)  # oldest first
        num_to_delete = len(files) - (MAX_MESSAGES - 1)
        for i in range(num_to_delete):
            try:
                print("Deleting old conversation:", files[i])
                os.remove(files[i])
            except Exception as e:
                print("WARNING: failed to delete", files[i], e)

    # Create a new file (timestamped)
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    filename = os.path.join(CONV_DIR, f"conversation_{timestamp}.json")

    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump([], f)   # start with empty list
        print("Created new conversation file:", filename)
    except Exception as e:
        print("ERROR: failed to create file:", filename, e)
        raise

    return filename


def save_conversation(filename, messages):
    try:
        with open(filename, "w") as f:
            json.dump(messages, f, indent=4)
    except Exception:
        print("Error saving conversation")
