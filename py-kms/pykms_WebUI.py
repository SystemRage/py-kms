import os, uuid, datetime
from flask import Flask, render_template
from pykms_Sql import sql_get_all
from pykms_DB2Dict import kmsDB2Dict

serve_count = 0

def _random_uuid():
    return str(uuid.uuid4()).replace('-', '_')

def _increase_serve_count():
    global serve_count
    serve_count += 1

def _get_serve_count():
    return serve_count

_kms_items = None
_kms_items_ignored = None
def _get_kms_items_cache():
    global _kms_items, _kms_items_ignored
    if _kms_items is None:
        _kms_items = {}
        _kms_items_ignored = 0
        queue = [kmsDB2Dict()]
        while len(queue):
            item = queue.pop(0)
            if isinstance(item, list):
                for i in item:
                    queue.append(i)
            elif isinstance(item, dict):
                if 'KmsItems' in item:
                    queue.append(item['KmsItems'])
                elif 'SkuItems' in item:
                    queue.append(item['SkuItems'])
                elif 'Gvlk' in item:
                    if len(item['Gvlk']):
                        _kms_items[item['DisplayName']] = item['Gvlk']
                    else:
                        _kms_items_ignored += 1
                #else:
                #    print(item)
            else:
                raise NotImplementedError(f'Unknown type: {type(item)}')
    return _kms_items, _kms_items_ignored

app = Flask('pykms_webui')
app.jinja_env.globals['start_time'] = datetime.datetime.now()
app.jinja_env.globals['get_serve_count'] = _get_serve_count
app.jinja_env.globals['random_uuid'] = _random_uuid

@app.route('/')
def root():
    _increase_serve_count()
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
        path='/',
        error=error,
        clients=clients,
        count_clients=countClients,
        count_clients_windows=countClientsWindows,
        count_clients_office=countClientsOffice,
        count_projects=len(_get_kms_items_cache()[0])
    )

@app.route('/license')
def license():
    _increase_serve_count()
    with open('../LICENSE', 'r') as f:
        return render_template(
            'license.html',
            path='/license/',
            license=f.read()
        )

@app.route('/products')
def products():
    _increase_serve_count()
    items, ignored = _get_kms_items_cache()
    countProducts = len(items)
    countProductsWindows = len([i for i in items if 'windows' in i.lower()])
    countProductsOffice = len([i for i in items if 'office' in i.lower()])
    return render_template(
        'products.html',
        path='/products/',
        products=items,
        filtered=ignored,
        count_products=countProducts,
        count_products_windows=countProductsWindows,
        count_products_office=countProductsOffice
    )
    