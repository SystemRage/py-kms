import os, uuid, datetime
from flask import Flask, render_template
from pykms_Sql import sql_get_all

serve_count = 0

def _random_uuid():
    return str(uuid.uuid4()).replace('-', '_')

def _get_serve_count():
    return serve_count

app = Flask('pykms_webui')
app.jinja_env.globals['start_time'] = datetime.datetime.now()
app.jinja_env.globals['get_serve_count'] = _get_serve_count
app.jinja_env.globals['random_uuid'] = _random_uuid

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
        'clients.html',
        error=error,
        clients=clients,
        count_clients=countClients,
        count_clients_windows=countClientsWindows,
        count_clients_office=countClientsOffice
    )

@app.route('/license')
def license():
    global serve_count
    serve_count += 1
    with open('../LICENSE', 'r') as f:
        return render_template(
            'license.html',
            license=f.read()
        )