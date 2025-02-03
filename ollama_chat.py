import json
import requests
import time
import gradio as gr

def fetch_models():
    url = "http://localhost:11434/api/tags"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return [model.get("name", "None") for model in data.get("models", [])]
    else:
        print("Failed to fetch models:", response.status_code)
        return []
    
def convert_to_chat_message(msg):
    if isinstance(msg, gr.ChatMessage):
        return msg
    elif isinstance(msg, dict):
        return gr.ChatMessage(
            content=msg.get("content", ""),
            role=msg.get("role", ""),
            metadata=msg.get("metadata", {}),
            options=msg.get("options", None)
        )
    return msg

def chatbot_response(message, history, selected_model):
    if history is None:
        history = []
    history = [convert_to_chat_message(msg) for msg in history]
    history = history + [gr.ChatMessage(content=message, role="user")]

    url = "http://localhost:11434/api/generate"
    headers = {"Content-Type": "application/json"}
    prompt = "\n".join([f"{msg.role}: {msg.content}" for msg in history if not msg.metadata])
    payload = {"model": selected_model, "stream": True, "prompt": prompt}
    response = requests.post(url, json=payload, stream=True, headers=headers)

    if response.status_code != 200:
        error_msg = f"Error: {response.status_code} - {response.text}"
        yield gr.ChatMessage(content=error_msg, role="assistant")
        return

    accumulated_text = ""
    thinking_message = None
    thinking_start_time = None
    end_thinking = False

    for line in response.iter_lines():
        if not line:
            continue
        try:
            decoded_line = line.decode("utf-8").strip()
            if not decoded_line:
                continue
            data = json.loads(decoded_line)
        except Exception as e:
            print("Error decoding line:", e)
            continue

        chunk = data.get("response", "")
        accumulated_text += chunk

        if accumulated_text.startswith("<think>") and "</think>" not in accumulated_text:
            if thinking_message is None:
                thinking_start_time = time.time()
                thinking_message = gr.ChatMessage(
                    content="",
                    metadata={"title": "Thinking...", "id": 0, "status": "pending"},
                )
            thinking_content = accumulated_text.split("<think>", 1)[1].strip()
            thinking_message.content = thinking_content
            yield thinking_message

        elif "</think>" in accumulated_text:
            end_thinking = True
            thinking_message.metadata["status"] = "done"
            thinking_message.metadata["time"] = time.time() - thinking_start_time
            if end_thinking:
                yield [thinking_message, gr.ChatMessage(content=accumulated_text.split("</think>")[1].strip(), role="assistant")]
        else:
            yield gr.ChatMessage(content=accumulated_text.strip(), role="assistant")

    if thinking_message is not None:
        yield [thinking_message, gr.ChatMessage(content=accumulated_text.split("</think>")[1].strip(), role="assistant")]
    else:
        yield gr.ChatMessage(content=accumulated_text.strip(), role="assistant")

with gr.Blocks() as demo:
    model_dropdown = gr.Dropdown(
        choices=fetch_models(),
        value="deepseek-r1:1.5b",  # default model
        label="Select Model"
    )
    gr.ChatInterface(
    fn=chatbot_response,
    additional_inputs=[model_dropdown],
    # chatbot=gr.Chatbot(
    #     height=600,
    #     placeholder="<strong>Your Personal AI assistance</strong><br>Ask Me Anything",
    #     render_markdown=True
    # ),
    type="messages",
    title="Ollama Chat with DeepSeek 14b",
    description="This is a local instance of DeepSeek 14b. Please ask me anything.",
    example_labels=["Verify model", "English-Spanish translator"],
    examples=[
        ["Who are you? What is your name?"],
        ["Act as translator, when I write something in English, you'll write its translation in Spanish and vice versa. Let's start: ¿Cómo está el clima?"],
    ],
    flagging_mode="manual",
    flagging_options=["Like", "Spam", "Inappropriate", "Other"],
    save_history=True,
)


if __name__ == "__main__":
    demo.launch()