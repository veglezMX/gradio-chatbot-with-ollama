from typing import Union, List, Optional
import gradio as gr

def convert_to_chat_message(
    msg: Union[gr.ChatMessage, dict, list]
) -> Union[gr.ChatMessage, List[gr.ChatMessage]]:
    """Convert various message formats to gr.ChatMessage."""
    if isinstance(msg, gr.ChatMessage):
        return msg
    if isinstance(msg, dict):
        return gr.ChatMessage(
            content=msg.get("content", ""),
            role=msg.get("role", "user"),
            metadata=msg.get("metadata", {}),
        )
    if isinstance(msg, list):
        return [convert_to_chat_message(m) for m in msg]
    raise ValueError(f"Unsupported message type: {type(msg)}")

def prepare_prompt(
    history: Optional[List[Union[gr.ChatMessage, dict, list]]], 
    user_message: str, 
    custom_instructions: str = ""
) -> str:
    """Prepare a prompt from chat history and the new user message."""
    history = history or []
    if custom_instructions:
        history.insert(0, gr.ChatMessage(content=custom_instructions, role="system"))
    
    chat_history: List[gr.ChatMessage] = []
    for msg in history:
        converted = convert_to_chat_message(msg)
        if isinstance(converted, list):
            chat_history.extend(converted)
        else:
            chat_history.append(converted)
    
    chat_history.append(gr.ChatMessage(content=user_message, role="user"))
    
    prompt = "\n".join(
        f"{msg.role}: {msg.content}"
        for msg in chat_history
        if not msg.metadata
    )
    return prompt
