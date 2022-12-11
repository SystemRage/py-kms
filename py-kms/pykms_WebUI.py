import os, uuid, datetime
from flask import Flask, render_template
from pykms_Sql import sql_get_all

app = Flask('pykms_webui')

start_time = datetime.datetime.now()
serve_count = 0

def _random_uuid():
    return str(uuid.uuid4()).replace('-', '_')

@app.route('/')
def root():
    global serve_count
    serve_count += 1
    error = None
    # Get the db name / path
    dbPath = None
    envVarName = 'PYKMS_SQLITE_DB_PATH'
    if envVarName in os.environ:
        dbPath = os.environ.get(envVarName)
    else:
        error = f'Environment variable is not set: {envVarName}'
    # Fetch all clients from the database.
    clients = None
    try:
        if dbPath:
            clients = sql_get_all(dbPath)
    except Exception as e:
        error = f'Error while loading database: {e}'
    countClients = len(clients) if clients else 0
    countClientsWindows = len([c for c in clients if c['applicationId'] == 'Windows']) if clients else 0
    countClientsOffice = countClients - countClientsWindows
    return render_template(
        'index.html',
        start_time=start_time.isoformat(),
        error=error,
        clients=clients,
        count_clients=countClients,
        count_clients_windows=countClientsWindows,
        count_clients_office=countClientsOffice,
        serve_count=serve_count,
        random_uuid=_random_uuid
    )