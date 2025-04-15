from src.common.env_setup import *
from src.lgraph.sql_analyzer import *
from src.lgraph.bq_client import BigQueryClient
from langgraph.graph import StateGraph, START, END
from langgraph.types import RetryPolicy
from src.lgraph.models import SqlImprovementState
import base64
from quart import Quart, render_template, request, jsonify
import asyncio
import signal
from langfuse.callback import CallbackHandler

credentials = setup_aiplatform()
logger = logging.getLogger(__name__)
langfuse_callback = setup_langfuse_callback()
llm = create_llm(callbacks=[langfuse_callback])
bq_client = BigQueryClient(project_id=GCP_PROJECT, credentials=credentials)
sql_analyzer = SqlAnalyzer(llm, bq_client)
app = Quart(__name__)


workflow = StateGraph(SqlImprovementState)
workflow.add_node("verify_sql", sql_analyzer.verify_and_run_original_sql)
workflow.add_node("identify_tables", sql_analyzer.get_table_info)
workflow.add_node("find_antipatterns", sql_analyzer.generate_info)
workflow.add_node("previous_optimizatons", sql_analyzer.get_previous_optimizations)
workflow.add_node("suggestions", sql_analyzer.get_suggestions)
workflow.add_node("optimize", sql_analyzer.get_optimized_query)
workflow.add_node("verify_optimized_sql", sql_analyzer.verify_and_run_optimized_sql)

workflow.add_edge(START, "verify_sql")
workflow.add_edge("verify_sql", "identify_tables")
workflow.add_edge("identify_tables", "find_antipatterns")
workflow.add_edge(
    "find_antipatterns", "previous_optimizatons"
)  # use search for similar previous usecases
workflow.add_edge("find_antipatterns", "suggestions")
workflow.add_edge("suggestions", "optimize")
workflow.add_edge("previous_optimizatons", "optimize")
workflow.add_edge("optimize", "verify_optimized_sql")  # use tools to verify the performance
workflow.add_conditional_edges(
    "verify_optimized_sql",
    sql_analyzer.llm_router,
    {"Continue": "find_antipatterns", "Finish": END},
)

app.chain = workflow.compile().with_config({"callbacks": [langfuse_callback]})
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
        state = await app.chain.ainvoke(
            sql,
            config={
                "metadata": {
                    "langfuse_user_id": "user-id",
                    "langfuse_session_id": "your-session-id",
                }
            },
        )
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
        loop.add_signal_handler(s, lambda s: asyncio.create_task(shutdown(loop, signal=s)))
    try:
        await app.run_task(debug=True, port=8880, host="0.0.0.0")
    finally:
        await shutdown(loop)


if __name__ == "__main__":
    asyncio.run(main())
