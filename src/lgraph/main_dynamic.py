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
from langchain.tools import Tool
from typing_extensions import Literal
from langgraph.types import Command


credentials = setup_aiplatform()
logger = logging.getLogger(__name__)
langfuse_callback = setup_langfuse_callback()
llm = create_llm(callbacks=[langfuse_callback])
bq_client = BigQueryClient(project_id=GCP_PROJECT, credentials=credentials)
sql_analyzer = SqlAnalyzer(llm, bq_client)
app = Quart(__name__)


async def query_run_and_stats(table_id: str):
    return bq_client.evaluate_query(await bq_client.execute_sql_query(table_id))


table_metadata_tool = Tool.from_function(
    coroutine=bq_client.get_table_metadata,
    func=bq_client.get_table_metadata,
    name="get_table_metadata",
    description="Fetch BigQuery table schema and stats.",
)

query_run_and_stats_tool = Tool.from_function(
    coroutine=query_run_and_stats,
    func=query_run_and_stats,
    name="query_run_and_stats",
    description="Run the BigQuery sql and calculates the stats",
)


async def planner_agent(
    state: SqlImprovementState,
) -> Command[Literal["plan_exectution_agent", "__end__"]]:
    if state["attempt"] > 3:
        return Command(goto=END, update={})

    previous_optimization = ""
    if state["attempt"] > 0:
        original_score = state.get("sql_res", {}).get("score", 0)
        optimized_score = state.get("optimized_sql_res", {}).get("score", 0)
        optimized_sql = state.get("optimized_sql", "")
        original_sql = state.get("sql", "")
        previous_optimization = f"""
        The original SQL had a performance score of {original_score:.3f}.
        The optimized SQL has a performance score of {optimized_score:.3f}.

        Original SQL:
        {original_sql}

        Optimized SQL:
        {optimized_sql}
    """

    planner_agent_prompt = f"""
    Based on the sql query, decide which of the tasks needs to be executed for optimization of the provided query:
    "get_tables","suggestions","optimized_query", "__end__".

    Input SQL:
        {state['sql']}

    Attempt: {state['attempt']}

    {previous_optimization}

    Allowed sequence:
        1) Dont optimize the query, since it's considered good enough (or Attempt > 2): "__end__";
        2) Go with a full circle of tasks to have a full context and data (if Attempt > 0): "get_tables" -> "suggestions" -> "optimized_query" -> "__end__";
        3) If you don't need table metadata: "suggestions" -> "optimized_query" -> "__end__";
        4) Go directly to optimize a query directly, if you know the problem already: "optimized_query" -> "__end__";
        5) You can also skip some of the sequnces, it's not required to be contigious, but "optimized_query" and "__end__" should always present:"optimized_query" -> "__end__".

    Respond only with one of the 5 allowed sequences, in the format like with 3: suggestions,optimized_query,__end__.
    If you see an optimized query where score is higher then original - go directly to option 1).
    Answer:
    """
    msg = await llm.ainvoke(planner_agent_prompt)
    choice = msg.content.strip().lower().split(",")
    return Command(goto="plan_exectution_agent", update={"exectution_plan": choice})


async def plan_exectution_agent(
    state: SqlImprovementState,
) -> Command[Literal["get_tables", "suggestions", "optimized_query", "planner_agent"]]:
    commands = state["exectution_plan"]
    next_command = commands[0]
    logger.info(commands)

    if next_command == "__end__":
        model_with_tools = llm.bind_tools([query_run_and_stats_tool])
        prompt = f"""
        Decide which query is better, evaluate the origial query (sql) and suggested query (optimized_sql) using stats in the following order sql, optimized_sql.
        sql:
        {state['sql']}

        optimized_sql:
        {state['optimized_sql']}
        """
        msg = await model_with_tools.ainvoke(prompt)
        update = {"attempt": state["attempt"] + 1, "exectution_plan": []}

        if msg.tool_calls:
            stats = await asyncio.gather(
                *(query_run_and_stats_tool.ainvoke(tool_call) for tool_call in msg.tool_calls)
            )
            for stat in stats:
                logger.info(stat.content)
                s = json.loads(stat.content)
                if s["metadata"]["sql"] == state["sql"]:
                    update["sql_res"] = s
                else:
                    update["optimized_sql_res"] = s

        return Command(goto="planner_agent", update=update)
    else:
        return Command(goto=next_command, update={"exectution_plan": commands[1:]})


async def get_table_info(state: SqlImprovementState) -> Command[Literal["plan_exectution_agent"]]:
    model_with_tools = llm.bind_tools([table_metadata_tool])
    prompt = f"""
        Extract all table names from the following SQL query and Fetch BigQuery table schema & stats.
        Return the fully-qualified table names in the format 'project.dataset.table_id' as a comma-separated list and apply corresponding tools.

        SQL Query: {state['sql']}
        """
    msg = await model_with_tools.ainvoke(prompt)
    if msg.tool_calls:
        tables = await asyncio.gather(
            *(table_metadata_tool.ainvoke(tool_call) for tool_call in msg.tool_calls)
        )
    return Command(
        goto="plan_exectution_agent", update={"tables": [json.loads(t.content) for t in tables]}
    )


async def get_suggestions(state: SqlImprovementState) -> Command[Literal["plan_exectution_agent"]]:
    msg = await llm.ainvoke(get_antipatterns_prompt(state["sql"]))
    antipatterns = []
    current_pattern = {}
    for line in msg.content.split("\n"):
        if not line:
            if current_pattern:
                antipatterns.append(current_pattern)
                current_pattern = {}
            continue
        line = line.strip()
        line = line.replace("*", "")
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip().upper()
            value = value.strip()
            if key in ["CODE", "NAME", "DESCRIPTION", "IMPACT", "LOCATION", "SUGGESTION"]:
                current_pattern[key.lower()] = value
    if current_pattern:
        antipatterns.append(current_pattern)
    return Command(goto="plan_exectution_agent", update={"antipatterns": antipatterns})


async def get_optimized_query(
    state: SqlImprovementState,
) -> Command[Literal["plan_exectution_agent"]]:
    # model_with_tools = llm.bind_tools([query_run_and_stats_tool])
    improvements = state.get("improvements") or None
    tables = state.get("tables") or None
    antipatterns = state.get("antipatterns") or None
    msg = await llm.ainvoke(
        get_optimized_sql_prompt2(state["sql"], improvements, antipatterns, tables)
    )

    def clean_sql_string(sql_string):
        return sql_string.replace("```sql", "").replace("```", "").strip()

    return Command(
        goto="plan_exectution_agent", update={"optimized_sql": clean_sql_string(msg.content)}
    )


graph = StateGraph(SqlImprovementState)
graph.add_node("planner_agent", planner_agent)
graph.add_node("plan_exectution_agent", plan_exectution_agent)
graph.add_node("get_tables", get_table_info)
graph.add_node("suggestions", get_suggestions)
graph.add_node("optimized_query", get_optimized_query)
graph.add_edge(START, "planner_agent")

app.chain = graph.compile().with_config({"callbacks": [langfuse_callback], "recursion_limit": 50})
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

    sql = SqlImprovementState(sql=sql.strip(), attempt=0, improvements=[])
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
