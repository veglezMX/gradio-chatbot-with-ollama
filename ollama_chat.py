import json
import requests
import gradio as gr

def get_available_models():
    url = "http://localhost:11434/api/models"
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Error fetching models: {response.status_code} - {response.text}")
            return []
        models = response.json()  # Assumes response is a JSON list/dict of models.
        return models
    except Exception as e:
        print("Exception retrieving models:", e)
        return []


def chatbot_response(message, history):
    # Ensure history is a list and append the user's message.
    if history is None:
        history = []
    # Append the user message (with role "user") to the conversation history.
    history = history + [gr.ChatMessage(content=message, role="user")]

    def get_role_and_content(msg):
        if isinstance(msg, dict):
            return msg.get("role", ""), msg.get("content", "")
        return msg.role, msg.content

    url = "http://localhost:11434/api/generate"
    headers = {"Content-Type": "application/json"}
    # Set stream=True so that the API sends chunks.
    
    prompt = "\n".join([f"{get_role_and_content(msg)[0]}: {get_role_and_content(msg)[1]}" for msg in history])
    payload = {"model": "llama3.2", "stream": True, "prompt": prompt}
    response = requests.post(url, json=payload, stream=True, headers=headers)

    if response.status_code != 200:
        error_msg = f"Error: {response.status_code} - {response.text}"
        yield history + [gr.ChatMessage(content=error_msg, role="assistant")]
        return

    # This variable will accumulate the bot's text.
    accumulated_text = ""

    # Process each streamed chunk.
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

        # Check whether the accumulated text contains the end marker for a thinking block.
        if "</think>" in accumulated_text:
            # Split the text into the thinking part and the actual response.
            thinking_part, actual_response = accumulated_text.split("</think>", 1)
            # Extract the content inside the <think> tag.
            if "<think>" in thinking_part:
                thinking_content = thinking_part.split("<think>", 1)[1].strip()
            else:
                thinking_content = thinking_part.strip()
            # Create a ChatMessage for the thinking subbox.
            thinking_msg = gr.ChatMessage(
                content=thinking_content,
                metadata={"title": "Thinking...", "id": 0, "status": "pending"},
                role="assistant"
            )
            # Create another ChatMessage for the actual final response.
            final_response_msg = gr.ChatMessage(
                content=actual_response.strip(),
                role="assistant"
            )
            # Yield the complete conversation history: user message plus two assistant messages.
            yield  [thinking_msg, final_response_msg]
            return
        else:
            # No complete thinking block yet; yield an intermediate update with the current accumulated text.
            intermediate_msg = gr.ChatMessage(content=accumulated_text, role="assistant")
            yield  [intermediate_msg]

    # If streaming ends and no thinking block was detected, yield the final message.
    final_msg = gr.ChatMessage(content=accumulated_text.strip(), role="assistant")
    yield  [final_msg]


# Create a ChatInterface with Gradio.
with gr.Blocks() as demo:
    model_dropdown = gr.Dropdown(
        choices=get_available_models(),
        value="llama3.2",  # default model
        label="Select Model"
    )
    chat_history = gr.Chatbot()
    text_input = gr.Textbox(placeholder="Enter message here...", label="Your Message")
    
    def process_message(message, history, selected_model):
        return chatbot_response(message, history, selected_model)
        
    send_button = gr.Button("Send")
    send_button.click(process_message, 
                      inputs=[text_input, chat_history, model_dropdown], 
                      outputs=chat_history)

demo.launch()

if __name__ == "__main__":
    demo.launch()
