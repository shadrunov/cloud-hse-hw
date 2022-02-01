import csv
import json
import os
import ssl
from io import StringIO
from asyncio import sleep
from typing import Dict
import logging

from aiohttp.client import ClientSession
from aiohttp.client_exceptions import ClientError
from fastapi import FastAPI, Request, Response
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler

CH_HOST = os.getenv("LOGBROKER_CH_HOST", "84.201.152.236")
CH_USER = os.getenv("LOGBROKER_CH_USER")
CH_PASSWORD = os.getenv("LOGBROKER_CH_PASSWORD")
CH_PORT = int(os.getenv("LOGBROKER_CH_PORT", 8123))
CH_CERT_PATH = os.getenv("LOGBROKER_CH_CERT_PATH")

LOG_FILE = os.getenv("LOG_FILE", "back/files/example.log")
DATA_FILE = os.getenv("DATA_FILE", "back/files/data.txt")
ERRORS_FILE = os.getenv("ERRORS_FILE", "back/files/errors.txt")
UNDELIVERED_FILE = os.getenv("UNDELIVERED_FILE", "back/files/undelivered.txt")
TABLE_FOR_UNDELIVERED = "kek"
TIME_INTERVAL = os.getenv("TIME_INTERVAL", 3)

BACK1_IP = os.getenv("BACK1_IP", '192.168.1.5')
BACK2_IP = os.getenv("BACK2_IP", '0.0.0.0:8000')

logging.basicConfig(filename=LOG_FILE, filemode="w", level=logging.INFO)


async def execute_query(query, data=None):
    url = f"http://{CH_HOST}:{CH_PORT}/"
    params = {"query": query.strip()}
    headers = {}
    if CH_USER is not None:
        headers["X-ClickHouse-User"] = CH_USER
        if CH_PASSWORD is not None:
            headers["X-ClickHouse-Key"] = CH_PASSWORD
    ssl_context = (
        ssl.create_default_context(cafile=CH_CERT_PATH) if CH_CERT_PATH is not None else None
    )

    async with ClientSession() as session:
        async with session.post(
            url, params=params, data=data, headers=headers, ssl=ssl_context, timeout=1
        ) as resp:
            await resp.read()
            logging.warning(f"{resp.status}")
            return await resp.text()

app = FastAPI()


@app.on_event("startup")
def init_data():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_to_db, "cron", second=f"*/{TIME_INTERVAL}")
    scheduler.start()
    logging.getLogger('apscheduler.executors.default').setLevel(logging.WARNING)


async def query_wrapper(query, data=None):
    await execute_query(query, data)


@app.get("/show_create_table")
async def show_create_table(table_name: str):
    resp = await execute_query(f'SHOW CREATE TABLE "{table_name}";')
    if isinstance(resp, str):
        return Response(content=resp.replace("\\n", "\n"), media_type="text/plain; charset=utf-8")
    return resp


async def send_csv(table_name: str, string_io: StringIO):
    string_io.seek(0)
    logging.info(f"send_csv - sending to db: {table_name, string_io.read()}")
    string_io.seek(0)
    try:
        await query_wrapper(f'INSERT INTO "{table_name}" FORMAT CSV', string_io)
    except Exception as e:
        logging.error(f"send_csv undelivered: {e.args}")
        with open(UNDELIVERED_FILE, "a+") as file:
            string_io.seek(0)
            file.write(string_io.read())
    else:
        logging.info("send_csv sent to db")


async def write_csv(string_io: StringIO, rows):
    cwr = csv.writer(string_io, quoting=csv.QUOTE_ALL)
    logging.debug(f"{rows}")
    for row in rows:
        if len(row) < 2:
            row.extend([""] * (2 - len(row)))
        logging.debug(f"write_csv - current row: {row}")

    logging.debug(f"write_csv - all rows: {rows}")
    cwr.writerows(rows)


async def write_json(string_io: StringIO, rows):
    prepared_csv = []
    for row in rows:
        assert isinstance(row, dict)
        row = [*row.values()]
        if len(row) < 2:
            row.extend([""] * (2 - len(row)))
        prepared_csv.append(row)
        logging.debug(f"write_json - current row: {row}")

    logging.debug(f"write_json - all rows: {prepared_csv}")
    await write_csv(string_io, prepared_csv)


async def send_to_db():
    # queue = {}
    queue: Dict[str, StringIO] = {}

    # try to resend undelivered logs
    undelivered_count, data_count = 0, 0
    with open(UNDELIVERED_FILE, "r+") as undelivered:
        for line in undelivered:

            table_name = TABLE_FOR_UNDELIVERED
            if table_name not in queue:
                queue[table_name] = StringIO()

            logging.debug(f"send_to_db - writing rows to csv: {table_name}")
            queue[table_name].write(line)
            undelivered_count += 1

        logging.info(f"write_log accessed: {undelivered_count} undelivered_rows processed")
        undelivered.truncate(0)

    with open(DATA_FILE, "r+") as data:
        for line in data:
            logging.debug(f"send_to_db - line: {line}")
            log_entry = json.loads(line)

            table_name = log_entry["table_name"]
            if table_name not in queue:
                queue[table_name] = StringIO()

            rows = log_entry["rows"]

            if log_entry.get("format") == "json":
                logging.debug(f"send_to_db - writing rows to json: {table_name, rows}")
                await write_json(queue[table_name], rows)

            elif log_entry.get("format") == "list":
                logging.debug(f"send_to_db - writing rows to csv: {table_name, rows}")
                await write_csv(queue[table_name], rows)
            data_count += 1

        logging.info(f"write_log accessed: {data_count} data_rows processed")
        data.truncate(0)

    for table_name in queue:
        logging.debug(
            f"send_to_db - sending rows to csv: {table_name, queue[table_name].readlines()}"
        )
        await send_csv(table_name, queue[table_name])
        if table_name != [*queue.keys()][-1]:  # if not last StringIO in queue
            await sleep(1)


@app.post("/write_log")
async def write_log(request: Request):
    body = await request.json()
    logging.info(f"write_log accessed: {body}")
    for log_entry in body:
        if (
            log_entry.get("format") in ("list", "json")
            and log_entry.get("table_name")
            and log_entry.get("rows")
        ):
            with open(DATA_FILE, "a") as data:
                data.write(json.dumps(log_entry))
                data.write("\n")
        else:
            with open(ERRORS_FILE, "a") as errors:
                errors.write(
                    f"error: unknown format {log_entry.get('format')}, you must use list or json \n"
                )
    return 200


@app.get("/healthcheck")
async def healthcheck():
    return Response(content="Ok", media_type="text/plain")


@app.get("/undelivered_internal")
async def undelivered_internal():
    logging.info("undelivered internal accessed")
    with open(UNDELIVERED_FILE, "r") as u:
        return Response(content=u.read(), media_type="text/plain")

@app.get("/undelivered")
async def undelivered():
    logging.info("undelivered accessed")
    undelivered = 'from 1 node: \n'
    try:
        async with ClientSession() as session:
            async with session.get(f'http://{BACK1_IP}/undelivered_internal', timeout=1) as resp:
                undelivered += await resp.text()
    except:
        pass

    undelivered += 'from 2 node: \n'
    try:
        async with ClientSession() as session:
            async with session.get(f'http://{BACK2_IP}/undelivered_internal', timeout=1) as resp:
                undelivered += await resp.text()
    except:
        pass

    return Response(content=undelivered, media_type="text/plain")


@app.get("/logs")
async def logs():
    with open(LOG_FILE, "r") as u:
        logging.info("logs accessed")
        return Response(content=u.read(), media_type="text/plain")
