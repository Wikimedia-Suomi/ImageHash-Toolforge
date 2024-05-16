import re
import toolforge
import pymysql.cursors
import threading
import pywikibot
import time
import hashlib
import imagehash
import requests
from datetime import datetime
from PIL import Image
from io import BytesIO

# Increase the max limit
Image.MAX_IMAGE_PIXELS = 10000*10000
site = pywikibot.Site('commons', 'commons')
print("Site")


def ping_databases():
    tools_conn.ping(reconnect=True)
    commons_conn.ping(reconnect=True)


def parse_date(int_date):
    str_date = int_date.decode('utf-8')
    return datetime.strptime(str_date, "%Y%m%d%H%M%S")


# DEPRECATED! Not all pages are in page table
def set_page_failed(conn, page_id):
    with conn.cursor() as cur:
        sql = 'UPDATE page SET enabled=-1 WHERE page_id=%(page_id)s'
        cur.execute(sql, {
            'page_id': int(page_id) 
        })
        conn.commit()


def is_dhash_in_db(conn, page_id, int_date):
    timestamp = parse_date(int_date)
    with conn.cursor() as cur:
        sql = 'SELECT hash FROM phash WHERE commons=%(page_id)s AND created>%(timestamp)s LIMIT 1'
        cur.execute(sql, {
            'page_id': int(page_id),
            'timestamp': timestamp,
        })
        rows = cur.fetchall() 
        for row in rows:
            if "hash" in row:
                return row["hash"]
    return None


def insert_dhash_to_db(conn, page_id, dhash, width, height, url, thumb_width, thumb_type):
    sql = 'INSERT INTO dhash (commons, hash, width, height, thumb_width, thumb_type) '
    sql += 'VALUES (%(page_id)s, %(dhash)s, %(width)s, %(height)s, %(thumb_width)s, %(thumb_type)s)'
    with conn.cursor() as cur:
        cur.execute(sql, {
            'page_id': int(page_id),
            'dhash': int(dhash),
            'width': int(width),
            'height': int(height),
            'thumb_width': thumb_width,
            'thumb_type': thumb_type
        })
        conn.commit()


def is_phash_in_db(conn, page_id, int_date):
    timestamp = parse_date(int_date)
    with conn.cursor() as cur:
        sql = 'SELECT hash FROM phash WHERE commons=%(page_id)s AND created>%(timestamp)s LIMIT 1'
        cur.execute(sql, {
            'page_id': int(page_id),
            'timestamp': timestamp
        })
        rows = cur.fetchall()
        for row in rows:
            if "hash" in row:
                return row["hash"]
    return None


def insert_phash_to_db(conn, page_id, phash, width, height, url, thumb_width, thumb_type):
    sql = 'INSERT INTO phash (commons, hash, width, height, thumb_width, thumb_type) VALUES '
    sql += '(%(page_id)s, %(phash)s, %(width)s, %(height)s, %(thumb_width)s, %(thumb_type)s)'
    with conn.cursor() as cur:
        cur.execute(sql, {
            'page_id': int(page_id),
            'phash': int(phash),
            'width': int(width),
            'height': int(height),
            'thumb_width': thumb_width,
            'thumb_type': thumb_type
        })
        conn.commit()


def load_image(url):
    headers = {
        'User-Agent': 'ImagehashBot/0.3 (https://fi.wikipedia.org/wiki/user:Zache)',
    }
    # Send a GET request to the image url
    response = requests.get(url, headers=headers)

    # Raise an error if the GET request was unsuccessful
    response.raise_for_status()

    # Open the image
    image = Image.open(BytesIO(response.content))

    # Return the image object
    return image


def extract_width_from_url(url):
    # Use regular expression to find numbers followed by 'px' in the URL
    pattern = r'/thumb/.*?/([^/]+-)?(\d+)px-[^/]+$'
    match = re.search(pattern, url)
    if match:
        return int(match.group(2))
    else:
        return None


def extract_thumbnail_type_from_url(url):
    # Regex pattern to match '/thumb/' followed by capturing the thumbnail type
    pattern = r'/thumb/.*?/([^/]+-)?\d+px-[^/]+$'

    # Search the URL with the regex pattern
    match = re.search(pattern, url)

    # Check if there's a match and return the captured group
    if match:
        thumb_type = match.group(1)
        if thumb_type is None:
            thumb_type = 'default'
            return thumb_type
        else:
            thumb_type = thumb_type.rstrip('-')
            allowed_types = ['lossy-page1', 'lossy-page2', 'lossless-page1']
            if thumb_type in allowed_types:
                return thumb_type
            else:
                return 'error'
    else:
        return None


def get_mediawiki_url(page_id, filename, width, height):
    target_width = 1024

    # Remove prefix and change underscores
    cleaned_filename = filename.replace("File:", "").strip()

    # Urlencode the filename
#    encoded_filename = urllib.parse.quote(cleaned_filename.replace(" ", "_"))
    encoded_filename = cleaned_filename.replace(" ", "_")

    # Calculate hash
    hash = hashlib.md5(encoded_filename.encode()).hexdigest()

    # Clean special characters
    encoded_filename = encoded_filename.replace('?', '%3F')
    encoded_filename = encoded_filename.replace(',', '%2C')

    # If width is large then return thumbnail url else return full image
    # large tiffs are more likely to fail than small tiffs
    if height*width > 5000*5000 and '.tif' in filename.lower():
        try:
            p = list(site.load_pages_from_pageids([page_id]))[0]
            p = pywikibot.FilePage(site, p.title())
            return p.get_file_url(url_width=1024)
        except:
            return None

    elif height * width > 5000 * 5000:
        target_width = 1024
        return f"https://upload.wikimedia.org/wikipedia/commons/thumb/{hash[0]}/{hash[0:2]}/{encoded_filename}/{target_width}px-{encoded_filename}"
    else:
        return f"https://upload.wikimedia.org/wikipedia/commons/{hash[0]}/{hash[0:2]}/{encoded_filename}"


# difference hashing
# http://www.hackerfactor.com/blog/index.php?/archives/529-Kind-of-Like-That.html
def calculate_dhash(im):
    hash = imagehash.dhash(im)
    hash_int = int(str(hash), 16)
    return hash_int


# Perceptual hashing
# http://www.hackerfactor.com/blog/index.php?/archives/432-Looks-Like-It.html
def calculate_phash(im):
    hash = imagehash.phash(im)
    hash_int = int(str(hash), 16)
    return hash_int


# Just debug print helper function
def print_t(str):
    # print(str)
    return None


# Return only page_ids without imagehash
def filter_page_ids(page_ids):
    filtered_page_ids = []

    if len(page_ids):
        with tools_conn.cursor() as tools_cur:
            seen_ids = set()
            sql = 'select commons from phash where commons IN %(page_ids)s'
            params = {
                'page_ids': page_ids
            }
            tools_cur.execute(sql, params)
            rows = tools_cur.fetchall()
            for row in rows:
                if row['commons'] not in seen_ids:
                    seen_ids.add(row['commons'])

            for page_id in page_ids:
                if page_id not in seen_ids:
                    filtered_page_ids.append(page_id)

    # There should be least one page_id in ret
    if not len(filtered_page_ids):
        filtered_page_ids.append(page_ids[0])

    return filtered_page_ids


# Return only page_ids for images without hash
# or hashis older than image
def filter_pages_using_timestamps(input_page_ids):
    page_ids = []
    if len(input_page_ids) == 0:
        page_ids.append(0)
        return page_ids

    with tools_conn.cursor() as tools_cur:
        sql = 'select commons as page_id,created from phash where commons IN %(page_ids)s'
        params = {
                'page_ids': list(input_page_ids.keys())
        }
        tools_cur.execute(sql, params)
        rows = tools_cur.fetchall()
        hashed_ids = {}
        for row in rows:
            hashed_ids[row['page_id']] = row['created']

    # Test if image is already hashed
    for page_id, ts1 in input_page_ids.items():
        if page_id not in hashed_ids:
            page_ids.append(page_id)
        else:
            ts2 = hashed_ids[page_id]
            if ts1 > ts2:
                page_ids.append(page_id)

    if len(page_ids) == 0:
        page_ids.append(0)

    return page_ids


# Get images
def get_image_data(page_ids, max_el_id):
    ret = []

    with commons_conn.cursor() as cur:
        sql = 'select page_id as rc_id, page_id, page_title, img_width, img_height, img_timestamp from page, image where page_title=img_name and page_namespace=6'
        sql = sql + ' and img_minor_mime IN %(img_minor_mime)s and page_id IN %(page_ids)s and img_width*img_height<%(max_size)s'
        params = {
            'max_size': 6000*6000,
            'page_ids': page_ids,
            'img_minor_mime': ['jpeg', 'webp', 'tiff']
        }
        cur.execute(sql, params)
        rows = cur.fetchall()
        for row in rows:
            row['rc_id'] = max_el_id
            ret.append(row)

    return ret


def get_pages(mode, min_id, filter_param):
    page_ids = []

    if mode == 'externallinks':
        new_min_id, unfiltered_page_ids = get_pages_by_externallinks(min_id, filter_param)
        page_ids = filter_page_ids(unfiltered_page_ids)

    elif mode == 'recentchanges':
        new_min_id, page_ids = get_pages_by_recentchanges(min_id)

    elif mode == 'page':
        new_min_id, page_ids = get_pages_by_page_table(min_id)

    images = get_image_data(page_ids, new_min_id)
    return new_min_id, images


def get_pages_by_externallinks(min_id, domain_filter):
    page_ids = [0]
    seen_ids = set()
    max_el_id = min_id

    # Test that domain filter is useful
    if not domain_filter or len(domain_filter) < 2:
        return max_el_id, page_ids

    with commons_conn.cursor() as cur:

        sql = 'select el_id, el_from as page_id from externallinks '
        sql += 'where (el_to_domain_index LIKE %(http_domain)s OR el_to_domain_index LIKE %(https_domain)s) '
        sql += 'and el_id>%(min_id)s order by el_id limit 100000'

        # domain_filter is reversed (ie. 'com.flickr')
        params = {
            'min_id': min_id,
            'http_domain': 'http://' + domain_filter + '%',
            'https_domain': 'https://' + domain_filter + '%'
        }

        try:
            cur.execute(sql, params)
            rows = cur.fetchall()
            for row in rows:
                # Just picking unique page_ids here as it is faster in python than in SQL
                if row['page_id'] not in seen_ids:
                    seen_ids.add(row['page_id'])
                    page_ids.append(row['page_id'])

                if row['el_id'] > max_el_id:
                    max_el_id = row['el_id']

        except Exception as e:
            expanded_sql = sql % {
                               'http_domain': "'" + params['http_domain'] + "'",
                               'https_domain': "'" + params['https_domain'] + "'",
                               'min_id': params['min_id']
                           }
            print(f"Failed to execute SQL query: {expanded_sql}")
            print("Error:", e)
            raise

    return max_el_id, page_ids


# Fetch images using recentchanges table
def get_pages_by_recentchanges(min_rc_id):
    page_ids = [0]
    rc_page_ids = {}
    max_rc_id = min_rc_id
    with commons_conn.cursor() as cur:
        sql = 'select rc_id, rc_cur_id as page_id, rc_timestamp from recentchanges where '
        sql += ' rc_log_type="upload" and rc_namespace = 6 '
        sql += ' and rc_log_action="upload" and rc_id>%(min_rc_id)s order by rc_id limit 100000'
        print(sql)

        cur.execute(sql, {
            'min_rc_id': min_rc_id,
        })
        rows = cur.fetchall()
        for row in rows:
            rc_page_ids[row['page_id']] = parse_date(row['rc_timestamp'])

            if row['rc_id'] > max_rc_id:
                max_rc_id = row['rc_id']

    page_ids = filter_pages_using_timestamps(rc_page_ids)
    return max_rc_id, page_ids


# fetch images using page and image table
def get_pages_by_page_table(min_page_id):
    page_ids = {}
    max_page_id = min_page_id
    with commons_conn.cursor() as cur:
        sql = 'SELECT page_id, img_timestamp FROM page,image WHERE '
        sql += 'img_name=page_title AND page_namespace=6 AND page_id>%(min_page_id)s '
        sql += 'ORDER BY page_id LIMIT 100000'
        cur.execute(sql, {
            'min_page_id': min_page_id,
        })
        rows = cur.fetchall()
        for row in rows:
            page_ids[row['page_id']] = parse_date(row['img_timestamp'])
            if row['page_id'] > max_page_id:
                max_page_id = row['page_id']

    ret_page_ids = filter_pages_using_timestamps(page_ids)
    return max_page_id, ret_page_ids


def handle_pages(pages):
    conn = toolforge.toolsdb('s55462__imagehash', cursorclass=pymysql.cursors.DictCursor)

    for page in pages:
        conn.ping(reconnect=True)
        start_time = time.time()
        start_time_total = time.time()

        page_id = page['page_id']
        page_title = page['page_title'].decode()
        page_width = page['img_width']
        page_height = page['img_height']
        page_timestamp = page['img_timestamp']
        dhash_in_db = is_dhash_in_db(conn, page_id, page_timestamp)
        phash_in_db = is_phash_in_db(conn, page_id, page_timestamp)

        if dhash_in_db and phash_in_db:
            continue

        try:
            image_url = get_mediawiki_url(page_id, page_title, page_width, page_height)
        except:
            print("get_mediawiki_url failed " + page_title)
            set_page_failed(conn, page_id)
            continue

        try:
            thumb_width = extract_width_from_url(image_url)
            thumb_type = extract_thumbnail_type_from_url(image_url)
        except:
            continue
        print(f'{thumb_width}\t{thumb_type}')
        try:
            headers = {
                'User-Agent': 'ImagehashBot/0.3 (https://fi.wikipedia.org/wiki/user:Zache)',
            }
            # Send a GET request to the image url
            response = requests.get(image_url, headers=headers)

            # Raise an error if the GET request was unsuccessful
            response.raise_for_status()

            # Open the image
            image = Image.open(BytesIO(response.content))
        except:
            print("error")
            if image_url:
                print("Image loading failed: " + image_url)
            set_page_failed(conn, page_id)
            time.sleep(10)
            continue

        loading_time = str(time.time() - start_time)
        print_t(page_title + "\ti " + str(time.time() - start_time))
        start_time = time.time()
        try:
            if not dhash_in_db:
                dhash_tmp = imagehash.dhash(image)
                dhash = int(str(dhash_tmp), 16)
                print_t(page_title + "\ti " + str(time.time() - start_time))
                start_time = time.time()

                insert_dhash_to_db(conn, page_id, dhash, page_width, page_height, image_url, thumb_width, thumb_type)
                print_t(page_title + "\tj " + str(time.time() - start_time))
                start_time = time.time()

            if not phash_in_db:
                phash_tmp = imagehash.phash(image)
                phash = int(str(phash_tmp), 16)
                print_t(page_title + "\tl " + str(time.time() - start_time))
                start_time = time.time()

                insert_phash_to_db(conn, page_id, phash, page_width, page_height, image_url, thumb_width, thumb_type)
                print_t(page_title + "\tm " + str(time.time() - start_time))
                start_time = time.time()

        except Exception as e:
            print(f"Hashing failed 2:{e}")
            set_page_failed(conn, page_id)

        print_t(page_title + "\to " + str(time.time() - start_time))
        print(page_title + "\tp " + str(time.time() - start_time_total) + "\t" + loading_time)


def add_last_processed_page_id(conn, page_id, keyword):
    sql = 'INSERT INTO status (keyword, last_processed_page_id) VALUES (%(keyword)s, %(page_id)s) ON DUPLICATE KEY UPDATE last_processed_page_id = VALUES(last_processed_page_id);'
    with conn.cursor() as cur:
        cur.execute(sql, {
            'page_id': int(page_id),
            'keyword': keyword
        })
        conn.commit()


def get_last_processed_page_id(conn, keyword):
    with conn.cursor() as cur:
        sql = 'select last_processed_page_id from status where keyword=%(keyword)s'
        cur.execute(sql, {
            'keyword': keyword
        })

        row = cur.fetchone()
        if row:
            return row['last_processed_page_id']
    return 0


# MAIN() #
tools_conn = toolforge.toolsdb('s55462__imagehash', cursorclass=pymysql.cursors.DictCursor)
commons_conn = toolforge.connect('commonswiki_p', cursorclass=pymysql.cursors.DictCursor)

start_time2 = time.time()

# Divide data to multiple threads
maxthreadsnum = 12

# How many iterations script will do
loopcount = 10

# Finna

#filter_param = 'fi.finna'
#mode = 'externallinks'

# Recentchanges
#filter_param = None
#mode = 'recentchanges'

# Loop through page table

filter_param = None
mode = 'page'

category_salt = '20240516'

# Just tracking last processed id in database
category = f'{filter_param}_{mode}_{category_salt}'
min_id = get_last_processed_page_id(tools_conn, category)
print("Starting")
print(min_id)

for n in range(0, loopcount):
    commons_conn.ping(reconnect=True)
    tools_conn.ping(reconnect=True)

    # get_pages('externallinks', min_id, 'com.flickr')
    min_id, pages = get_pages(mode, min_id, filter_param)
    if len(pages) == 0:
        time.sleep(1)
        print("no pages")
        continue

    threadsnum = maxthreadsnum

    if len(pages) < maxthreadsnum:
        threadsum = 1

    print(f'min_id: {min_id}\tnumber of pages: {len(pages)}')

    itemcount = int(len(pages)/threadsnum)
    threads = []

    # Split to threads
    for n in range(0, threadsnum):
        t = pages[itemcount*n:itemcount*(n+1)]
        threads.append(threading.Thread(target=handle_pages, args=(t,)))

    # Start all threads
    for thread in threads:
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    handle_pages(pages)
    tools_conn.ping(reconnect=True)

    # Update last processed row_id to database
    add_last_processed_page_id(tools_conn, min_id, category)
    print(time.time() - start_time2)

print(time.time() - start_time2)
