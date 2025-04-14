from collections.abc import Callable

import gradio as gr


def build_demo(fn: Callable, examples: list):
    """
    Constructs a Gradio demo featuring a ChatInterface for generating SQL queries.

    This function creates a Gradio interface a ChatInterface
    component.  The ChatInterface is designed to allow users to interact with a
    function that generates message response, providing a chat-like experience.

    Args:
        fn (Callable): the function to wrap the chat interface around. Normally (assuming `type` is set to "messages"), the function should accept two parameters: a `str` representing the input message and `list` of openai-style dictionaries: {"role": "user" | "assistant", "content": `str` | {"path": `str`} | `gr.Component`} representing the chat history. The function should return/yield a `str` (for a simple message), a supported Gradio component (e.g. gr.Image to return an image), a `dict` (for a complete openai-style message response), or a `list` of such messages.
        examples (list): A list of example conversations to display in the
            ChatInterface.

    Returns:
        gradio.Blocks: A Gradio Blocks object representing the constructed demo.
            This object can be used to launch the interface.
    """
    with gr.Blocks(theme="ocean", fill_height=True) as demo:
        with gr.Row():
            with gr.Column():
                gr.Markdown("<center><h2>Write a SQL query for optimization</h2></center>")
                gr.ChatInterface(
                    fn=fn,
                    examples=examples,
                    type="messages",
                )
    return demo
