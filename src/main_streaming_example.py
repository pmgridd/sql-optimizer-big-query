from flask import Flask, render_template
from flask_sock import Sock
import json
import asyncio
from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

app = Flask(__name__)
sock = Sock(app)

clients = []


def broadcast(message):
    for client in clients:
        try:
            client.send(json.dumps(message))
        except Exception as e:
            print(f"Error sending message: {e}")


def process_data(state):
    result = f"Processed: {state['input']}"
    broadcast({"node": "process_data", "message": result})
    return {"result": result}


def finalize(state):
    message = "Workflow complete!"
    broadcast({"node": "finalize", "message": message})
    return {}


class SqlImprovementState(TypedDict):
    input: str
    result: str


workflow = StateGraph(SqlImprovementState)
workflow.add_node("process_data", process_data)
workflow.add_node("finalize", finalize)
workflow.set_entry_point("process_data")
workflow.add_edge("process_data", "finalize")
workflow.add_edge("finalize", END)
app_workflow = workflow.compile()


@app.route("/")
def index():
    return render_template("index_streaming.html")


@sock.route("/ws")
def websocket(ws):
    clients.append(ws)
    try:
        while True:
            data = ws.receive()
            input_data = json.loads(data)
            app_workflow.invoke({"input": input_data["message"]})
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        clients.remove(ws)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8880)
