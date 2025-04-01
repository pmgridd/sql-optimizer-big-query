import signal
import asyncio

from quart import Quart, request, jsonify
from src.crewai.analyze_sql_flow import SqlAnalysisFlow
from src.common.env_setup import *
from src.crewai.sql_optimizer_crew import SqlAnalysisCrew


credentials = setup_aiplatform()
app = Quart(__name__)
logger = logging.getLogger(__name__)


@app.route("/analyze", methods=["GET"])
async def analyze():
    sql = request.args.get("sql")
    if not sql or not sql.strip():
        return jsonify({"error": "SQL query cannot be empty!"}), 400

    try:
        flow = SqlAnalysisFlow()
        flow.state["sql"] = sql.strip()
        final_output = await flow.kickoff_async()
        return jsonify(final_output)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/analyze_crew", methods=["GET"])
async def analyze_crew():
    sql = request.args.get("sql")
    if not sql or not sql.strip():
        return jsonify({"error": "SQL query cannot be empty!"}), 400

    try:
        final_output = await SqlAnalysisCrew.crew().kickoff_async()
        return jsonify(final_output)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


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
