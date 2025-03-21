import os
import logging
from src.env_setup import *
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from typing_extensions import TypedDict
from src.utils import get_antipatterns_prompt
from src.sql_analyzer import *
from flask import Flask, render_template, request, jsonify
from src.bq_client import BigQueryClient
from langgraph.graph import StateGraph, START, END
from src.models import SqlImprovementState, SchemaInfo
import base64

credentials = setup_airplatform()
logger = logging.getLogger(__name__)
llm = create_llm()
bq_client = BigQueryClient(project_id=GCP_PROJECT, credentials=credentials)
sql_analyzer = SqlAnalyzer(llm, bq_client)
app = Flask(__name__)


def check_optimization(state: SqlImprovementState):
    """Gate check if continue sql improvement"""
    if len(state["tabels"]) > 0:
        return "Continue"
    return "Finish"


workflow = StateGraph(SqlImprovementState)
workflow.add_node("identify_tables", sql_analyzer.get_table_info)
workflow.add_node("antipatterns", sql_analyzer.generate_info)
workflow.add_node("suggestions", sql_analyzer.get_suggestions)

workflow.add_edge(START, "identify_tables")
workflow.add_conditional_edges(
    "identify_tables", check_optimization, {"Continue": "antipatterns", "Finish": END}
)
workflow.add_edge("antipatterns", "suggestions")
workflow.add_edge("suggestions", END)
chain = workflow.compile()


@app.route("/", methods=["GET", "POST"])
def index():
    graph_image = chain.get_graph().draw_mermaid_png()
    image_base64 = base64.b64encode(graph_image).decode("utf-8")
    return render_template("index.html", image_base64=image_base64)


@app.route("/analyze", methods=["GET"])
def analyze():
    sql = request.args.get("sql")
    if not sql or not sql.strip():
        return jsonify({"error": "SQL query cannot be empty!"}), 400

    sql = SqlImprovementState(sql=sql.strip())
    state = chain.invoke(sql)
    return jsonify(state)


def main():
    app.run(debug=True, port=8880, host="0.0.0.0")


if __name__ == "__main__":
    main()
