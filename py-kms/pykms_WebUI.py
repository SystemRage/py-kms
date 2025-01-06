import os, uuid, datetime
from flask import Flask, render_template
from pykms_Sql import sql_get_all
from pykms_DB2Dict import kmsDB2Dict

def _random_uuid():
    return str(uuid.uuid4()).replace('-', '_')

_serve_count = 0
def _increase_serve_count():
    global _serve_count
    _serve_count += 1

def _get_serve_count():
    return _serve_count

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
app.jinja_env.globals['version_info'] = None

_version_info_path = os.environ.get('PYKMS_VERSION_PATH', '../VERSION')
if os.path.exists(_version_info_path):
    with open(_version_info_path, 'r') as f:
        app.jinja_env.globals['version_info'] = {
            'hash': f.readline().strip(),
            'branch': f.readline().strip()
        }

_dbEnvVarName = 'PYKMS_SQLITE_DB_PATH'
def _env_check():
    if _dbEnvVarName not in os.environ:
        raise Exception(f'Environment variable is not set: {_dbEnvVarName}')

@app.route('/')
def root():
    _increase_serve_count()
    error = None
    # Get the db name / path
    dbPath = None
    if _dbEnvVarName in os.environ:
        dbPath = os.environ.get(_dbEnvVarName)
    else:
        error = f'Environment variable is not set: {_dbEnvVarName}'
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
    ), 200 if error is None else 500

@app.route('/readyz')
def readyz():
    try:
        _env_check()
    except Exception as e:
        return f'Whooops! {e}', 503
    if (datetime.datetime.now() - app.jinja_env.globals['start_time']).seconds > 10: # Wait 10 seconds before accepting requests
        return 'OK', 200
    else:
        return 'Not ready', 503

@app.route('/livez')
def livez():
    try:
        _env_check()
        return 'OK', 200 # There are no checks for liveness, so we just return OK
    except Exception as e:
        return f'Whooops! {e}', 503

@app.route('/license')
def license():
    _increase_serve_count()
    with open(os.environ.get('PYKMS_LICENSE_PATH', '../LICENSE'), 'r') as f:
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
    