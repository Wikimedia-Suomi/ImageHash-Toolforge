from flask import Flask, request, json, jsonify, send_from_directory, render_template
from urllib.parse import quote, quote_plus
import toolforge
import pymysql.cursors
import time
import hashlib
import requests
import imagehash
from PIL import Image
from io import BytesIO

app = Flask(__name__, static_folder='/data/project/imagehash/www/python/src/static')
commons_conn = toolforge.connect('commonswiki_p', cursorclass=pymysql.cursors.DictCursor)
tools_conn = toolforge.toolsdb('s55462__imagehash', cursorclass=pymysql.cursors.DictCursor)


# Perceptual hashing 
# http://www.hackerfactor.com/blog/index.php?/archives/432-Looks-Like-It.html

def calculate_phash(im):
    hash = imagehash.phash(im)
    hash_int=int(str(hash),16)
    return hash_int

# difference hashing
# http://www.hackerfactor.com/blog/index.php?/archives/529-Kind-of-Like-That.html

def calculate_dhash(im):
    hash = imagehash.dhash(im)
    hash_int=int(str(hash),16)
    return hash_int

# urlencode Finna parameters
def finna_api_parameter(name, value):
   return "&" + quote_plus(name) + "=" + quote_plus(value)


# Get finna API record with most of the information
# Finna API documentation
# * https://api.finna.fi
# * https://www.kiwi.fi/pages/viewpage.action?pageId=53839221 

def get_finna_record(id):

    url="https://api.finna.fi/v1/record?id=" +  quote_plus(id)
    url+= finna_api_parameter('field[]', 'geoLocations')
    url+= finna_api_parameter('field[]', 'id')
    url+= finna_api_parameter('field[]', 'title')
    url+= finna_api_parameter('field[]', 'subTitle')
    url+= finna_api_parameter('field[]', 'summary')
    url+= finna_api_parameter('field[]', 'buildings')
    url+= finna_api_parameter('field[]', 'formats')
    url+= finna_api_parameter('field[]', 'imageRights')
    url+= finna_api_parameter('field[]', 'images')
    url+= finna_api_parameter('field[]', 'imagesExtended')
    url+= finna_api_parameter('field[]', 'onlineUrls')
    url+= finna_api_parameter('field[]', 'openUrl')
    url+= finna_api_parameter('field[]', 'nonPresenterAuthors')
    url+= finna_api_parameter('field[]', 'onlineUrls')
    url+= finna_api_parameter('field[]', 'subjects')
    url+= finna_api_parameter('field[]', 'classifications')
    url+= finna_api_parameter('field[]', 'events')
    url+= finna_api_parameter('field[]', 'identifierString')

    try:
        response = requests.get(url)
        return response.json()
    except:
        print("Finna API query failed: " + url)
        return None


def get_thumbnail_url(filename, width=220):
    encoded_filename = quote(filename.replace(" ", "_"))
    hash = hashlib.md5(filename.replace(" ", "_").encode()).hexdigest()
    return f"https://upload.wikimedia.org/wikipedia/commons/thumb/{hash[0]}/{hash[0:2]}/{encoded_filename}/{width}px-{encoded_filename}"

def get_pageinfo(page_ids):
    ret=[]

    # If page_ids is empty then exit
    if len(page_ids)==0:
        return ret

    sql = "SELECT page_id, page_title FROM page WHERE page_namespace=6 AND page_id IN %(page_ids)s"
    with commons_conn.cursor() as commons_cursor:
        commons_cursor.execute(sql, {'page_ids':page_ids})
        results = commons_cursor.fetchall()

        for result in results:
            r={
                'page_id':int(result['page_id']), 
                'page_title':'File:' + result['page_title'].decode(),
                'thumbnail':get_thumbnail_url(result['page_title'].decode())
            }
            ret.append(r)
    return ret

def get_page_id(page_title):
    if page_title:
        sql = "SELECT page_id FROM page WHERE page_namespace=6 AND page_title=%(page_title)s"
        prefixlist = [ "File:", "file:", "Image:", "image:" ]
        for removeprefix in prefixlist:
            page_title=page_title.replace(removeprefix, "").strip()
        page_title=page_title.replace(" ", "_")
        with commons_conn.cursor() as commons_cursor:
            commons_cursor.execute(sql, {'page_title': page_title})
            result = commons_cursor.fetchone()

            if result:
                return result['page_id']

    return None

def do_phash_and_dhash_search(phash, dhash, maxdifference=3):
    # Create the SQL query with parameter placeholders
    sql = """

    # First use phash as reference point

    SELECT p1.commons AS commons1, p2.commons AS commons2, BIT_COUNT(d1.hash ^ d2.hash) AS bit_count
    FROM phash AS p1, dhash AS d1, phash AS p2, dhash AS d2
    WHERE
    p1.commons=d1.commons
    AND p1.hash=%(phash)s
    AND p1.hash=p2.hash
    AND p2.commons=d2.commons
    AND BIT_COUNT(d1.hash ^ d2.hash) < %(maxdifference)s

    UNION

    # Then same query but using dhash as reference point

    SELECT p1.commons AS commons1, p2.commons AS commons2, BIT_COUNT(p1.hash ^ p2.hash) AS bit_count
    FROM phash AS p1, dhash AS d1, phash AS p2, dhash AS d2
    WHERE
    p1.commons=d1.commons
    AND d1.hash=%(dhash)s
    AND d1.hash=d2.hash
    AND p2.commons=d2.commons
    AND BIT_COUNT(p1.hash ^ p2.hash) < %(maxdifference)s

    """

    params = {'dhash': dhash, 'phash': phash, 'maxdifference':maxdifference}

    with tools_conn.cursor() as cursor:
        cursor.execute(sql, params)
        results = cursor.fetchall()

    # Convert the results to a list of dictionaries for the response
    page_ids=[]
    for result in results:
        page_ids.append(result['commons1'])
        page_ids.append(result['commons2'])

    return page_ids


@app.route('/')
def index():
    greeting = 'usage: https://imagehash.toolforge.org/search?dhash=994677375445601741&phash=16302499845690113328&maxdifference=3'
    username = None
    return render_template(
        'index.html', username=username, greeting=greeting)
#   return 'usage: https://imagehash.toolforge.org/search?dhash=994677375445601741&phash=16302499845690113328&maxdifference=3'

@app.route('/externallinks')
def externallinks():
    times=[]
    start_time = time.time()

    # Reconnect to db if needed
    commons_conn.ping(reconnect=True)
    times.append(time.time() - start_time)

    # Extract query parameters
    debug = request.args.get('debug')
    el_to_domain_index = request.args.get('el_to_domain_index')
    el_to_path = request.args.get('el_to_path')

    # Ensure both parameters are provided
    if el_to_domain_index is None and el_to_path is None:
        return jsonify({'error': 'Missing el_to_domain_index and el_to_path parameters. Example: https://imagehash.toolforge.org/externallinks?el_to_domain_index=fi.finna&el_to_path=museovirasto.DCCAB48D57705BAA2ADD460616E764F6 '}), 400

    if el_to_domain_index is None:
        return jsonify({'error': 'Missing el_to_domain_index parameter. Example value: fi.finna. See https://www.mediawiki.org/wiki/Manual:Externallinks_table '}), 400

    if len(el_to_domain_index) < 3 and el_to_domain_index[0] != "%":
        return jsonify({'error': 'el_to_domain_index parameter is too short. Example value: fi.finna. See https://www.mediawiki.org/wiki/Manual:Externallinks_table'}), 400

    if el_to_path is None:
        return jsonify({'error': 'Missing el_to_path parameter. Example query: museovirasto.DCCAB48D57705BAA2ADD460616E764F6 ; See https://www.mediawiki.org/wiki/Manual:Externallinks_table'}), 400

    if len(el_to_path) < 3:
        return jsonify({'error': 'el_to_path parameter is too short. Example value: museovirasto.DCCAB48D57705BAA2ADD460616E764F6 ; See https://www.mediawiki.org/wiki/Manual:Externallinks_table'}), 400

    sql = """
         SELECT page_id
         FROM externallinks, page
         WHERE
         page_id=el_from
         AND page_namespace=6
         AND (
             el_to_domain_index LIKE %(https_el_to_domain_index)s
             OR
             el_to_domain_index LIKE %(http_el_to_domain_index)s
         )
         AND el_to_path LIKE %(el_to_path)s
         GROUP BY page_id
         LIMIT 100
         """
    with commons_conn.cursor() as cursor:
        params = {
            'https_el_to_domain_index': 'https://' + el_to_domain_index +'%',
            'http_el_to_domain_index': 'http://' + el_to_domain_index +'%',
            'el_to_path': '%' + el_to_path +'%'
        }
        cursor.execute(sql, params)
        results = cursor.fetchall()
    times.append(time.time() - start_time)

    # Convert the results to a list of dictionaries for the response
    page_ids=[]
    for result in results:
        page_ids.append(result['page_id'])

    # Format output
    ret = get_pageinfo(page_ids)

    times.append(time.time() - start_time)

    # If debug then show timing information in response
    if debug:
        ret.append(times)

    # Use Flask's json.dumps with indent parameter for pretty printing
    response = app.response_class(
        response=json.dumps(ret, indent=4),
        status=200,
        mimetype='application/json'
    )
    return response


@app.route('/search')
def search():
    times=[]
    start_time = time.time()

    # Reconnect to db if needed
    tools_conn.ping(reconnect=True)
    commons_conn.ping(reconnect=True)
    times.append(time.time() - start_time)

    # Extract query parameters
    dhash = request.args.get('dhash')
    phash = request.args.get('phash')
    maxdifference = request.args.get('maxdifference')
    debug = request.args.get('debug')

    # Ensure both parameters are provided
    if dhash is None or phash is None:
        return jsonify({'error': 'Missing dhash or phash parameter'}), 400

    if maxdifference is None:
        maxdifference = 3

    if not debug is None:
        debug = True

    # Validate that dhash and phash are integers
    try:
        dhash = int(dhash)
        phash = int(phash)
    except ValueError:
        return jsonify({'error': 'dhash and phash must be integers'}), 400

    try:
        maxdifference = int(maxdifference)
    except ValueError:
        return jsonify({'error': 'maxdifference must be integer'}), 400

    times.append(time.time() - start_time)

    # Get page_ids of similar images
    page_ids=do_phash_and_dhash_search(phash, dhash, maxdifference)
    times.append(time.time() - start_time)

    # Format output
    ret = get_pageinfo(page_ids)

    times.append(time.time() - start_time)

    # If debug then show timing information in response
    if debug:
        ret.append(times)

    # Use Flask's json.dumps with indent parameter for pretty printing
    response = app.response_class(
        response=json.dumps(ret, indent=4),
        status=200,
        mimetype='application/json'
    )
    return response

@app.route('/pagesearch')
def pagesearch():
    times=[]
    start_time = time.time()

    # Reconnect to db if needed
    tools_conn.ping(reconnect=True)
    commons_conn.ping(reconnect=True)
    times.append(time.time() - start_time)

    # Extract query parameters
    page_id = request.args.get('page_id')
    page_title = request.args.get('page_title')
    maxdifference = request.args.get('maxdifference')
    debug = request.args.get('debug')

    # Ensure both parameters are provided
    if page_id is None and page_title is None:
        return jsonify({'error': 'Missing page_id or page_title parameter'}), 400

    if maxdifference is None:
        maxdifference = 3

    if not debug is None:
        debug = True

    # Validate that dhash and phash are integers
    if page_title:
        page_id = get_page_id(page_title)
        if page_id is None:
            return jsonify({'error': 'No page found with the provided title'}), 404

    try:
        page_id = int(page_id)
    except ValueError:
        return jsonify({'error': 'page_id must be integers'}), 400

    try:
        maxdifference = int(maxdifference)
    except ValueError:
        return jsonify({'error': 'maxdifference must be integer'}), 400

    times.append(time.time() - start_time)

    # Create the SQL query with parameter placeholders
    sql = """

    # First use phash as reference point

    SELECT p1.commons AS commons1, p2.commons AS commons2, BIT_COUNT(d1.hash ^ d2.hash) AS bit_count
    FROM phash AS p1, dhash AS d1, phash AS p2, dhash AS d2 
    WHERE
    p1.commons=d1.commons
    AND p1.commons = %(page_id)s
    AND p1.hash=p2.hash
    AND p2.commons=d2.commons
    AND BIT_COUNT(d1.hash ^ d2.hash) < %(maxdifference)s

    UNION

    # Then same query but using dhash as reference point

    SELECT p1.commons AS commons1, p2.commons AS commons2, BIT_COUNT(p1.hash ^ p2.hash) AS bit_count
    FROM phash AS p1, dhash AS d1, phash AS p2, dhash AS d2
    WHERE
    p1.commons=d1.commons
    AND d1.commons = %(page_id)s
    AND d1.hash=d2.hash
    AND p2.commons=d2.commons
    AND BIT_COUNT(p1.hash ^ p2.hash) < %(maxdifference)s

    """

    params = {'page_id': page_id, 'maxdifference':maxdifference}

    with tools_conn.cursor() as cursor:
        cursor.execute(sql, params)
        results = cursor.fetchall()
    times.append(time.time() - start_time)

    # Convert the results to a list of dictionaries for the response
    page_ids=[]
    for result in results:
        page_ids.append(result['commons1'])
        page_ids.append(result['commons2'])

    times.append(time.time() - start_time)

    # Format output
    ret = get_pageinfo(page_ids)

    times.append(time.time() - start_time)

    # If debug then show timing information in response
    if debug:
        ret.append(times)

    # Use Flask's json.dumps with indent parameter for pretty printing
    response = app.response_class(
        response=json.dumps(ret, indent=4),
        status=200,
        mimetype='application/json'
    )
    return response

@app.route('/finnasearch')
def finnasearch():
    times=[]
    start_time = time.time()

    # Reconnect to db if needed
    tools_conn.ping(reconnect=True)
    commons_conn.ping(reconnect=True)
    times.append(time.time() - start_time)

    # Extract query parameters
    finna_id = request.args.get('finna_id')
    maxdifference = request.args.get('maxdifference')
    debug = request.args.get('debug')

    # Ensure both parameters are provided
    if finna_id is None:
        return jsonify({'error': 'Missing finna_id parameter'}), 400

    if maxdifference is None:
        maxdifference = 3

    if not debug is None:
        debug = True

    # Validate that dhash and phash are integers

    try:
        maxdifference = int(maxdifference)
    except ValueError:
        return jsonify({'error': 'maxdifference must be integer'}), 400

    finna_record = get_finna_record(finna_id)
    times.append(time.time() - start_time)

    if finna_record['status']!='OK':
        print("Skipping (status not OK): " + finna_id)
        return jsonify({'error': 'Finna record not found'}), 404

    if finna_record['resultCount']!=1:
        return jsonify({'error': 'Multiple Finna records found'}), 404

    imagesExtended=finna_record['records'][0]['imagesExtended'][0]
    finna_thumbnail_url="https://finna.fi" + imagesExtended['urls']['small']
#    finna_thumbnail_url="https://finna.fi" + imagesExtended['urls']['large']

    times.append(time.time() - start_time)

    response = requests.get(finna_thumbnail_url)
    im1 = Image.open(BytesIO(response.content))
#    im1 = Image.open(urllib.request.urlopen(finna_thumbnail_url))
    phash=calculate_phash(im1)
    dhash=calculate_dhash(im1)

    times.append(time.time() - start_time)

    # Get page_ids of similar images
    page_ids=do_phash_and_dhash_search(phash, dhash, maxdifference)
    times.append(time.time() - start_time)

    # Format output
    ret = get_pageinfo(page_ids)

    times.append(time.time() - start_time)

    # If debug then show timing information in response
    if debug:
        ret.append(times)

    # Use Flask's json.dumps with indent parameter for pretty printing
    response = app.response_class(
        response=json.dumps(ret, indent=4),
        status=200,
        mimetype='application/json'
    )
    return response


if __name__ == "__main__":
    app.run(debug=True)

