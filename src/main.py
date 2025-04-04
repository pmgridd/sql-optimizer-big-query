import os
import logging
from src.env_setup import *
from langchain_core.messages import HumanMessage
from typing_extensions import TypedDict
from src.sql_analyzer import *
from src.bq_client import BigQueryClient
from langgraph.graph import StateGraph, START, END
from langgraph.types import RetryPolicy
from src.models import SqlImprovementState, SchemaInfo
import base64
from quart import Quart, render_template, request, jsonify
import asyncio
import signal

credentials = setup_airplatform()
logger = logging.getLogger(__name__)
llm = create_llm()
bq_client = BigQueryClient(project_id=GCP_PROJECT, credentials=credentials)
sql_analyzer = SqlAnalyzer(llm, bq_client)
app = Quart(__name__)


def check_success(state: SqlImprovementState):
    """Gate check if sql succesfully optimized"""
    # if (state['optimized_sql_res']['score'] <= state['sql_res']['score']):
    #     return "Finish"
    # else:
    #     return "Continue"
    return "Finish"


workflow = StateGraph(SqlImprovementState)
workflow.add_node("verify_sql", sql_analyzer.verify_and_run_original_sql)
workflow.add_node("identify_tables", sql_analyzer.get_table_info)
workflow.add_node("antipatterns", sql_analyzer.generate_info)
workflow.add_node("previous_optimizatons", sql_analyzer.get_previous_optimizations)
workflow.add_node("suggestions", sql_analyzer.get_suggestions)
workflow.add_node("optimize", sql_analyzer.get_optimized_query)
workflow.add_node("verify_optimized_sql", sql_analyzer.verify_and_run_optimized_sql)

workflow.add_edge(START, "verify_sql")
workflow.add_edge("verify_sql", "identify_tables")
workflow.add_edge("identify_tables", "antipatterns")
workflow.add_edge(
    "antipatterns", "previous_optimizatons"
)  # use search for similar previous usecases
workflow.add_edge("previous_optimizatons", "optimize")
workflow.add_edge("previous_optimizatons", "suggestions")
workflow.add_edge("optimize", "verify_optimized_sql")  # use tools to verify the performance
workflow.add_conditional_edges(
    "verify_optimized_sql", check_success, {"Continue": "antipatterns", "Finish": END}
)

app.chain = workflow.compile()
app.chain.retry_policy = RetryPolicy()


@app.route("/", methods=["GET", "POST"])
async def index():
    try:
        graph_image = app.chain.get_graph().draw_mermaid_png()
        image_base64 = base64.b64encode(graph_image).decode("utf-8")
    except Exception as e:
        logging.info(f"Error while generating graph: {e}")
        image_base64 = None
    return await render_template("index.html", image_base64=image_base64)


@app.route("/analyze", methods=["GET"])
async def analyze():
    sql = request.args.get("sql")
    if not sql or not sql.strip():
        return jsonify({"error": "SQL query cannot be empty!"}), 400

    sql = SqlImprovementState(sql=sql.strip())
    try:
        state = await app.chain.ainvoke(sql)
        if "error" in state:
            return jsonify(state), 400
        return jsonify(state)
    except Exception as e:
        return jsonify({"error": f"{e}"}), 400


async def shutdown(loop, signal=None):
    """Cleanup tasks tied to the application's shutdown."""
    if signal:
        logging.info(f"Received exit signal {signal.name}...")
    logging.info("Performing cleanup tasks...")
    logging.info("Asyncio event loop stopped")
    tasks = [t for t in asyncio.all_tasks(loop=loop) if t is not asyncio.current_task()]
    [task.cancel() for task in asyncio.as_completed(tasks)]
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()


async def main():
    loop = asyncio.get_running_loop()
    # Register signals to shutdown gracefully
    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    for s in signals:
        loop.add_signal_handler(s, lambda s=s: asyncio.create_task(shutdown(loop, signal=s)))
    try:
        await app.run_task(debug=True, port=8880, host="0.0.0.0")
    finally:
        await shutdown(loop)


if __name__ == "__main__":
    asyncio.run(main())
