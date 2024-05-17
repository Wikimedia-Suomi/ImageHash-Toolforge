import os
import toolforge
import pymysql.cursors
import threading
#import concurrent.futures
#import pywikibot
import time
import hashlib
import urllib
import imagehash
import requests
from datetime import datetime
from PIL import Image
from io import BytesIO
import pywikibot

# Increase the max limit
Image.MAX_IMAGE_PIXELS = 800000000

site = pywikibot.Site('commons', 'commons')


def ping_databases():
    tools_conn.ping(reconnect=True)
    commons_conn.ping(reconnect=True)

def get_next_page_id():
    with tools_conn.cursor() as cur:
        sql='select page_id from page where enabled=1 and (phash_done=0 or dhash_done=0) limit 1'
        cur.execute(sql)
        row=cur.fetchone()
        if row:
            return row['page_id']

def get_page_title(page_id):
    with commons_conn.cursor() as cur:
        sql='select page_id, page_title, img_width, img_height from page, image '
#        sql=sql + 'where page_id=%(page_id)s and page_namespace=6 and page_title=img_name and (640/img_width*img_height)<480  and (img_width = 1024 or img_width>1500) and img_minor_mime IN %(img_minor_mime)s'
#        sql=sql + 'where page_id=%(page_id)s and page_namespace=6 and page_title=img_name and (640/img_width*img_height)<480 and img_width<1301 and img_minor_mime IN %(img_minor_mime)s'
#        sql=sql + 'where page_id=%(page_id)s and page_namespace=6 and page_title=img_name and (640/img_width*img_height)>479 and img_height<1301 and img_minor_mime IN %(img_minor_mime)s'
#        sql=sql + 'where page_id=%(page_id)s and page_namespace=6 and page_title=img_name and (640/img_width*img_height)>479 and img_height<8000 and img_minor_mime IN %(img_minor_mime)s'
        sql=sql + 'where page_id=%(page_id)s and page_namespace=6 and page_title=img_name and img_minor_mime IN %(img_minor_mime)s AND img_width<10000 AND img_height<10000'
        cur.execute(sql, {
            'page_id':int(page_id),
            'img_minor_mime':[ 'jpeg', 'webp', 'tiff']
        })
        row=cur.fetchone()
        if row:
            return row['page_title'].decode(), row['img_width'], row['img_height']
        else:
            return None, None, None

def parse_date(int_date):
    str_date = int_date.decode('utf-8')
    return datetime.strptime(str_date, "%Y%m%d%H%M%S")

def set_busy_page(page_id):
    with tools_conn.cursor() as cur:
        sql='UPDATE page SET enabled=2 WHERE page_id=%(page_id)s'
        cur.execute(sql, {
            'page_id':int(page_id)
        })
        tools_conn.commit()

def set_skip_page(page_id):
    with tools_conn.cursor() as cur:
        sql='UPDATE page SET enabled=0 WHERE page_id=%(page_id)s'
        cur.execute(sql, {
            'page_id':int(page_id)
        })
        tools_conn.commit()

def set_page_failed(conn, page_id):
    with conn.cursor() as cur:
        sql='UPDATE page SET enabled=-1 WHERE page_id=%(page_id)s'
        cur.execute(sql, {
            'page_id':int(page_id)
        })
        conn.commit()

def set_dhash_done(conn, page_id):
    with conn.cursor() as cur:
        sql='UPDATE page SET dhash_done=1 WHERE page_id=%(page_id)s'
        cur.execute(sql, {
            'page_id':int(page_id)
        })
        conn.commit()

def set_phash_done(conn, page_id):
    with conn.cursor() as cur:
        sql='UPDATE page SET phash_done=1 WHERE page_id=%(page_id)s'
        cur.execute(sql, {
            'page_id':int(page_id)
        })
        conn.commit()

def is_dhash_in_db(conn, page_id, int_date):
    timestamp=parse_date(int_date)
    with conn.cursor() as cur:
        sql='SELECT hash FROM phash WHERE commons=%(page_id)s AND type=%(type)s AND source LIKE %(source)s AND created>%(timestamp)s LIMIT 1'
        cur.execute(sql, {
            'page_id':int(page_id),
            'type':'1024px',
            'source':'imagehashpy%',
            'timestamp':timestamp,
#            'type':'320px'
        })
        rows = cur.fetchall()
        for row in rows:
            if "hash" in row:
                return row["hash"]
    return None




def insert_dhash_to_db(conn, page_id, dhash, width, height,url):
    sql='INSERT INTO dhash (commons, hash, type, source, width, height, url) VALUES (%(page_id)s, %(dhash)s, %(type)s, %(source)s, %(width)s, %(height)s, %(url)s)'
    with conn.cursor() as cur:
        cur.execute(sql, {
            'page_id':int(page_id),
            'dhash':int(dhash),
            'type':'1024px',
#            'type':'320px',
            'source':'imagehashpy kb',
            'width': int(width),
            'height': int(height),
            'url': url
        })
        conn.commit()

def is_phash_in_db(conn, page_id, int_date):
    timestamp=parse_date(int_date)
    with conn.cursor() as cur:
        sql='SELECT hash FROM phash WHERE commons=%(page_id)s AND type=%(type)s AND source LIKE %(source)s AND created>%(timestamp)s LIMIT 1'
        cur.execute(sql, {
            'page_id':int(page_id),
            'type':'1024px',
            'source':'imagehashpy%',
            'timestamp':timestamp

#            'type':'320px'
        })
        rows = cur.fetchall()
        for row in rows:
           if "hash" in row:
              return row["hash"]
    return None

def insert_phash_to_db(conn, page_id, phash, width, height,url):
    sql='INSERT INTO phash (commons, hash, type, source, width, height, url) VALUES (%(page_id)s, %(phash)s, %(type)s, %(source)s, %(width)s, %(height)s, %(url)s)'
    with conn.cursor() as cur:
        cur.execute(sql, {
            'page_id':int(page_id),
            'phash':int(phash),
            'type':'1024px',
#            'type':'320px',
            'source':'imagehashpy kb',
            'width': int(width),
            'height': int(height),
            'url': url
        })
        conn.commit()

def load_image(url):
    headers = {
        'User-Agent': 'ImagehashBot/0.2 (https://fi.wikipedia.org/wiki/user:Zache)',
    }
    # Send a GET request to the image url
    response = requests.get(url, headers=headers)

    # Raise an error if the GET request was unsuccessful
    response.raise_for_status()

    # Open the image
    image = Image.open(BytesIO(response.content))

    # Return the image object
    return image

def get_mediawiki_url(page_id, filename, width, height):
    target_width=1024
    
    # Remove prefix and change underscores
    cleaned_filename = filename.replace("File:", "").strip()

    # Urlencode the filename
#    encoded_filename = urllib.parse.quote(cleaned_filename.replace(" ", "_"))
    encoded_filename = cleaned_filename.replace(" ", "_")

    # Calculate hash
    hash = hashlib.md5(encoded_filename.encode()).hexdigest()
    encoded_filename=encoded_filename.replace('?', '%3F')
    encoded_filename=encoded_filename.replace(',', '%2C')

    # If width then return thumbnail url else return full image
    if height*width > 4000*4000 and '.tif' in filename.lower():
        p=list(site.load_pages_from_pageids([page_id]))[0]
        p=pywikibot.FilePage(site, p.title())
        return p.get_file_url(url_width=1024)
    elif height*width > 4000*4000 :
        target_width=1024
        return f"https://upload.wikimedia.org/wikipedia/commons/thumb/{hash[0]}/{hash[0:2]}/{encoded_filename}/{target_width}px-{encoded_filename}"
    else:
        return f"https://upload.wikimedia.org/wikipedia/commons/{hash[0]}/{hash[0:2]}/{encoded_filename}"


def get_filenames_petscan():
    filenames = []
    # Load the list of files
    file_list_url = "https://petscan.wmflabs.org/?psid=25144331&format=plain"
    response = requests.get(file_list_url)

    # Make sure the request was successful
    if response.status_code == 200:
        # Split the response text into lines to get a list of filenames
        filenames = response.text.split("\n")
    else:
        print("Failed to load file list")
    return filenames

# difference hashing
# http://www.hackerfactor.com/blog/index.php?/archives/529-Kind-of-Like-That.html

def calculate_dhash(im):
    hash = imagehash.dhash(im)
    hash_int=int(str(hash),16)
    return hash_int

# Perceptual hashing
# http://www.hackerfactor.com/blog/index.php?/archives/432-Looks-Like-It.html

def calculate_phash(im):
    hash = imagehash.phash(im)
    hash_int=int(str(hash),16)
    return hash_int

def print_t(str):
#    print(str)
    return None

# Main loop
def handle_image(n):
    print_t("---")
    start_time_total = time.time()
    start_time = time.time()
    page_id = get_next_page_id()
    if not page_id:
        print("All queued page_ids are done")
        exit(0)

    print_t(str(page_id) + "\ta " + str(time.time() - start_time))
    start_time=time.time()
    set_busy_page(page_id)

    print_t(str(page_id) + "\tb " + str(time.time() - start_time))
    start_time=time.time()

    page_title, orig_width, orig_height = get_page_title(page_id)
    if not page_title:
#        print("Error: Page title is missing " + str(page_id))
#        set_page_failed(page_id)
        return False

    print_t(str(page_id) + "\tc " + str(time.time() - start_time))
    start_time=time.time()

    dhash_in_db=is_dhash_in_db(page_id)
    print_t(str(page_id) + "\td " + str(time.time() - start_time))
    start_time=time.time()

    phash_in_db=is_phash_in_db(page_id)
    print_t(str(page_id) + "\te " + str(time.time() - start_time))
    start_time=time.time()

    if dhash_in_db and phash_in_db:
        print("phash and dhash already in db")
        set_dhash_done(page_id)
        set_phash_done(page_id)
        return False

    print_t(page_title + "\tf " + str(time.time() - start_time))
    start_time=time.time()

    image_url=get_mediawiki_url(page_id,page_title,orig_width, orig_height)
    print_t(image_url)
    print_t(page_title + "\tg " + str(time.time() - start_time))
    start_time=time.time()

    try:
#        image=load_image(image_url)
        headers = {
            'User-Agent': 'ImagehashBot/0.2 (https://fi.wikipedia.org/wiki/user:Zache)',
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
            print("Image loading failed: " +  image_url)
        set_page_failed(page_id)
        return False

    loading_time= str(time.time() - start_time)
    print_t(page_title + "\th " + loading_time)

    start_time=time.time()

    width, height = image.size

    try:
#        print("hashing")
        if not dhash_in_db:
#            print("dhash")
            dhash_tmp = imagehash.dhash(image)
            dhash=int(str(dhash_tmp),16)
#            dhash=calculate_dhash(image)
            print_t(page_title + "\ti " + str(time.time() - start_time))
            start_time=time.time()

            insert_dhash_to_db(page_id, dhash, width, height, image_url)
            print_t(page_title + "\tj " + str(time.time() - start_time))
            start_time=time.time()

            set_dhash_done(page_id)
            print_t(page_title + "\tk " + str(time.time() - start_time))
            start_time=time.time()


        if not phash_in_db:
#            print("phash")
            phash_tmp = imagehash.phash(image)
            phash=int(str(phash_tmp),16)
#            phash=calculate_phash(image)
            print_t(page_title + "\tl " + str(time.time() - start_time))
            start_time=time.time()

            insert_phash_to_db(page_id, phash, width, height, image_url)
            print_t(page_title + "\tm " + str(time.time() - start_time))
            start_time=time.time()

            set_phash_done(page_id)
            print_t(page_title + "\tn " + str(time.time() - start_time))
            start_time=time.time()

#        print("hashing done")

    except:
        print("Hashing failed")
        set_page_failed(page_id)

    print_t(page_title + "\to " + str(time.time() - start_time))
    print(page_title + "\tp " + str(time.time() - start_time_total) + "\t" + loading_time)
    start_time=time.time()
    return True

def get_target_ids(min_page_id=0, limit=1000000):
    ret=[]
    with tools_conn.cursor() as cur:
        sql='select page_id from page where enabled=1 and (phash_done=0 or dhash_done=0) and page_id>%(min_page_id)s order by page_id limit %(limit)s '
        cur.execute(sql, {
            'min_page_id':int(min_page_id),
            'limit':int(limit)
        })

        rows = cur.fetchall()
        for row in rows:
           if "page_id" in row:
              ret.append(row["page_id"])
    return ret

def get_pages_by_cat(category, min_page_id):
    ret=[]
    with commons_conn.cursor() as cur:
        sql='select page_id, page_title, img_width,img_height from categorylinks, page, image '
        sql= sql + 'where page_id=cl_from and page_namespace=6 and img_name=page_title and cl_to=%(category)s and page_id>%(min_page_id)s and img_minor_mime IN %(img_minor_mime)s and img_width<4000 and img_height<4000  order by page_id limit 10000'
        cur.execute(sql, {
            'category':category,
            'min_page_id':min_page_id,
            'img_minor_mime':[ 'jpeg', 'webp', 'tiff']
        })
        rows = cur.fetchall()
        for row in rows:
            ret.append(row)
    return ret

def get_pages_by_logging(min_id):
    ret=[]
    with commons_conn.cursor() as cur:
#        sql='select rc_id, rc_cur_id as page_id, rc_title as page_title, img_width, img_height, img_timestamp from recentchanges, image where img_name=rc_title and rc_log_type="upload" and rc_namespace = 6 ' 
##        sql= sql + ' and rc_log_action="upload" and rc_id>%(min_rc_id)s and img_minor_mime IN %(img_minor_mime)s and img_width<4000 and img_height<4000 order by rc_id limit 10000'
#        sql= sql + ' and rc_log_action="upload" and rc_id>%(min_rc_id)s and img_minor_mime IN %(img_minor_mime)s order by rc_id limit 10000'

        sql='select log_id as id, page_id, page_title, img_width, img_height, img_timestamp from logging, page, image where log_page=page_id and page_title=img_name and page_namespace=6 '
        sql=sql + ' and img_minor_mime IN %(img_minor_mime)s and log_action!="upload" and log_type="upload" and log_id>%(min_id)s order by log_id limit 10000'
        cur.execute(sql, {
            'min_id':min_id,
            'img_minor_mime':[ 'jpeg', 'webp', 'tiff']
        })
        rows = cur.fetchall()
        for row in rows:
            ret.append(row)
    return ret

def get_pages_by_externallinks(min_id):
    ret=[]
    with commons_conn.cursor() as cur:
#        sql='select rc_id, rc_cur_id as page_id, rc_title as page_title, img_width, img_height, img_timestamp from recentchanges, image where img_name=rc_title and rc_log_type="upload" and rc_namespace = 6 ' 
##        sql= sql + ' and rc_log_action="upload" and rc_id>%(min_rc_id)s and img_minor_mime IN %(img_minor_mime)s and img_width<4000 and img_height<4000 order by rc_id limit 10000'
#        sql= sql + ' and rc_log_action="upload" and rc_id>%(min_rc_id)s and img_minor_mime IN %(img_minor_mime)s order by rc_id limit 10000'

#select el_id, el_from from externallinks where (el_to_domain_index LIKE "http://com.flickr%" OR el_to_domain_index LIKE "https://com.flickr%") AND el_id > 1000000 limit 1000000

        sql='select el_id as id, page_id, page_title, img_width, img_height, img_timestamp from externallinks, page, image where el_from=page_id and page_title=img_name and page_namespace=6 '
        sql=sql + ' and img_minor_mime IN %(img_minor_mime)s and (el_to_domain_index LIKE %(http_domain)s OR el_to_domain_index LIKE %(https_domain)s) and el_id>%(min_id)s order by el_id limit 100000'
        cur.execute(sql, {
            'min_id':min_id,
            'img_minor_mime':[ 'jpeg', 'webp', 'tiff'],
            'http_domain': 'http://se%',
            'https_domain': 'https://se%'
        })
        rows = cur.fetchall()
        for row in rows:
            ret.append(row)
    return ret

def get_pages_by_recentchanges(min_rc_id):
    ret=[]
    with commons_conn.cursor() as cur:
        sql='select rc_id, rc_cur_id as page_id, rc_title as page_title, img_width, img_height, img_timestamp from recentchanges, image where img_name=rc_title and rc_log_type="upload" and rc_namespace = 6 ' 
#        sql= sql + ' and rc_log_action="upload" and rc_id>%(min_rc_id)s and img_minor_mime IN %(img_minor_mime)s and img_width<4000 and img_height<4000 order by rc_id limit 10000'
        sql= sql + ' and rc_log_action="upload" and rc_id>%(min_rc_id)s and img_minor_mime IN %(img_minor_mime)s order by rc_id limit 10000'

        cur.execute(sql, {
            'min_rc_id':min_rc_id,
            'img_minor_mime':[ 'jpeg', 'webp', 'tiff']
        })
        rows = cur.fetchall()
        for row in rows:
            ret.append(row)
    return ret


def get_pages(page_ids):
    ret=[]
    if len(page_ids)==0:
        return ret

    with commons_conn.cursor() as cur:
#        sql='select page_id, page_title, img_width, img_height from page,image where page_namespace=6 and page_title=img_name and page_id IN %(page_ids)s'
        sql='select page_id, page_title, img_width, img_height from page,image where page_namespace=6 and page_title=img_name and page_id IN %(page_ids)s'
        sql= sql + ' and ((img_width<img_height and img_height<6000) or (img_width>=img_height and img_width<6000)) and img_minor_mime IN %(img_minor_mime)s'
#        sql= sql + ' and (img_width>img_height and img_width>1999)  and img_minor_mime IN %(img_minor_mime)s'
        cur.execute(sql, {
            'page_ids':page_ids,
            'img_minor_mime':[ 'jpeg', 'webp', 'tiff']
        })

        rows = cur.fetchall()
        for row in rows:
              ret.append(row)
    return ret


def handle_pages(pages):
    conn = toolforge.toolsdb('s55462__imagehash', cursorclass=pymysql.cursors.DictCursor)

    for page in pages:
        conn.ping(reconnect=True)
        start_time=time.time()
        start_time_total=time.time()

        page_id=page['page_id']
        page_title=page['page_title'].decode()
        page_width=page['img_width']
        page_height=page['img_height']
        page_timestamp=page['img_timestamp']
        dhash_in_db=is_dhash_in_db(conn, page_id, page_timestamp)
        phash_in_db=is_phash_in_db(conn, page_id, page_timestamp)

        if dhash_in_db and phash_in_db:
            continue

        image_url=get_mediawiki_url(page_id, page_title,page_width, page_height)
        try:
            headers = {
                'User-Agent': 'ImagehashBot/0.2 (https://fi.wikipedia.org/wiki/user:Zache)',
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
                print("Image loading failed: " +  image_url)
            set_page_failed(conn, page_id)
            time.sleep(10)
            continue

        loading_time=str(time.time() - start_time)
        print_t(page_title + "\ti " + str(time.time() - start_time))   
        start_time=time.time()
        try:
            if not dhash_in_db:
                dhash_tmp = imagehash.dhash(image)
                dhash=int(str(dhash_tmp),16)
                print_t(page_title + "\ti " + str(time.time() - start_time))
                start_time=time.time()

                insert_dhash_to_db(conn, page_id, dhash, page_width, page_height, image_url)
                print_t(page_title + "\tj " + str(time.time() - start_time))
                start_time=time.time()

                set_dhash_done(conn, page_id)
                print_t(page_title + "\tk " + str(time.time() - start_time))
                start_time=time.time()


            if not phash_in_db:
                phash_tmp = imagehash.phash(image)
                phash=int(str(phash_tmp),16)
                print_t(page_title + "\tl " + str(time.time() - start_time))
                start_time=time.time()

                insert_phash_to_db(conn, page_id, phash, page_width, page_height, image_url)
                print_t(page_title + "\tm " + str(time.time() - start_time))
                start_time=time.time()

                set_phash_done(conn, page_id)
                print_t(page_title + "\tn " + str(time.time() - start_time))
                start_time=time.time()

        except:
            print("Hashing failed")
            set_page_failed(conn, page_id)

        print_t(page_title + "\to " + str(time.time() - start_time))
        print(page_title + "\tp " + str(time.time() - start_time_total) + "\t" + loading_time)


def add_last_processed_page_id(conn, page_id, keyword):
    sql='INSERT INTO status (keyword, last_processed_page_id) VALUES (%(keyword)s, %(page_id)s) ON DUPLICATE KEY UPDATE last_processed_page_id = VALUES(last_processed_page_id);'
    with conn.cursor() as cur:
        cur.execute(sql, {
            'page_id':int(page_id),
            'keyword': keyword
        })
        conn.commit()

def get_last_processed_page_id(conn, keyword):
    with conn.cursor() as cur:
        sql='select last_processed_page_id from status where keyword=%(keyword)s'
        cur.execute(sql, {
            'keyword': keyword
        })

        row=cur.fetchone()
        if row:
            return row['last_processed_page_id']
    return 0

## MAIN() ##
tools_conn = toolforge.toolsdb('s55462__imagehash', cursorclass=pymysql.cursors.DictCursor)
commons_conn = toolforge.connect('commonswiki_p', cursorclass=pymysql.cursors.DictCursor)

start_time2 = time.time()

# Divide data into three parts
threadsnum=4
batchsize=100
loopcount=1
loopcount=5000
batchsize=10000
category='externallinks_finna5'
min_id=get_last_processed_page_id(tools_conn, category)

for n in range(0,loopcount):
    commons_conn.ping(reconnect=True)
    tools_conn.ping(reconnect=True)

    pages = get_pages_by_externallinks(min_id)
    for p in pages:
        if p['id']>min_id:
            min_id=p['id']
    print(len(pages))
    print(min_id)
    if len(pages)==0:
        break

    itemcount=int(len(pages)/threadsnum)
    threads=[]

    # Split to threads
    for n in range(0,threadsnum):
        t=pages[itemcount*n:itemcount*(n+1)]
        threads.append(threading.Thread(target=handle_pages, args=(t,)))

    # Start all threads
    for thread in threads:
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    tools_conn.ping(reconnect=True)
    add_last_processed_page_id(tools_conn, min_id, category)
#for n in range(0,10):
#    handle_image(n)
#    break

# Loop through the filenames
#with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
#    future_to_url = {executor.submit(handle_image, n): n for n in range(0,10)}

#    for future in concurrent.futures.as_completed(future_to_url):
#        try:
#        image = future.result()
#        except Exception as exc:
#                print('generated an exception: %s' % (exc))

print(time.time() - start_time2)

