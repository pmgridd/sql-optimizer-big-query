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
import json
from langgraph.graph import StateGraph, START, END
from IPython.display import Image, display
from src.models import SqlImprovementState, SchemaInfo


credentials = setup_airplatform()
logger = logging.getLogger(__name__)
llm = create_llm()
bq_client = BigQueryClient(project_id=GCP_PROJECT, credentials=credentials)
sql_analyzer = SqlAnalyzer(llm, bq_client)
app = Flask(__name__)


def check_optimization(state: SqlImprovementState):
    """Gate check if continue sql improvement"""

    # Simple check - does the joke contain "?" or "!"
    if len(state["tabels"]) > 0:
        return "Pass"
    return "Fail"


workflow = StateGraph(SqlImprovementState)
workflow.add_node("identify_tables", sql_analyzer.get_table_info)
workflow.add_node("antipatterns", sql_analyzer.generate_info)
workflow.add_node("suggestions", sql_analyzer.get_suggestions)

workflow.add_edge(START, "identify_tables")
workflow.add_conditional_edges(
    "identify_tables", check_optimization, {"Pass": "antipatterns", "Fail": END}
)
workflow.add_edge("antipatterns", "suggestions")
workflow.add_edge("suggestions", END)
chain = workflow.compile()
display(Image(chain.get_graph().draw_mermaid_png()))


class SqlImprovementState(TypedDict):
    sql: str
    improvements: list[dict]


@app.route("/", methods=["GET", "POST"])
def home():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    query = request.form.get("sql_query", "").strip()
    # "select * from adp_rnd_dwh_performance.catalog_sales s inner join adp_rnd_dwh_performance.call_center c on s.id = c.id where apg is null;"
    sql = SqlImprovementState(sql=query)

    state = chain.invoke(sql)

    print(print(json.dumps(state, indent=4)))

    if not query:
        return jsonify({"error": "SQL query cannot be empty!"})

    return jsonify(
        {
            "suggestions": json.dumps(state["suggestions"], indent=4),
            "improvements": json.dumps(state["antipattterns"], indent=4),
            "performance": {},
        }
    )


def main():
    # sql = SqlImprovementState(sql="select * from adp_rnd_dwh_performance.catalog_sales s inner join adp_rnd_dwh_performance.call_center c on s.id = c.id where apg is null;")

    # res = sql_analyzer.get_table_info(sql)
    # sql = sql | res

    # res = sql_analyzer.generate_info(sql)
    # sql = sql | res

    # res = sql_analyzer.get_suggestions(sql)
    # sql = sql | res

    # print(print(json.dumps(sql, indent=4)))

    app.run(debug=True, port=8880, host="0.0.0.0")


if __name__ == "__main__":
    main()

# docker build -t langgraph_demo -f docker/Dockerfile .
# docker run -p 8880:8880 --env-file .env langgraph_demo
