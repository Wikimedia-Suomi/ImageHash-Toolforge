Toolforge Imagehash batch job indexing code. 

### Running standalone

Indexing requires access to Wikimedia labs commons database replica and tools database. Documentation expects that code is running in the Wikimedia Cloud service virtual server.


```
# python3 -m venv venv
# source venv/bin/activate
# pip install --upgrade pip
# pip install -r requirements.txt
# python run_imagehash_index.py
# deactivate
```

### Database configuration
Commons replica and toolsdb database configuration works in same way than in Toolforge. Database configuration file is:

~/replica.my.cnf

```
[client]
user = dbusername
password = dbpassword
```

### Database tables

```
describe phash;
+-------------+--------------------------------------------------------------+------+-----+---------------------+----------------+
| Field       | Type                                                         | Null | Key | Default             | Extra          |
+-------------+--------------------------------------------------------------+------+-----+---------------------+----------------+
| id          | int(11)                                                      | NO   | PRI | NULL                | auto_increment |
| commons     | int(11)                                                      | YES  | MUL | NULL                |                |
| hash        | bigint(20) unsigned                                          | YES  | MUL | NULL                |                |
| width       | int(11)                                                      | YES  |     | NULL                |                |
| height      | int(11)                                                      | YES  |     | NULL                |                |
| created     | timestamp                                                    | NO   |     | current_timestamp() |                |
| thumb_width | int(11)                                                      | YES  |     | NULL                |                |
| thumb_type  | enum('default','lossy-page1','lossy-page2','lossless-page1') | YES  |     | NULL                |                |
+-------------+--------------------------------------------------------------+------+-----+---------------------+----------------+
8 rows in set (0.001 sec)

describe dhash;
+-------------+----------------------------------------------------------------------+------+-----+---------------------+----------------+
| Field       | Type                                                                 | Null | Key | Default             | Extra          |
+-------------+----------------------------------------------------------------------+------+-----+---------------------+----------------+
| id          | int(11)                                                              | NO   | PRI | NULL                | auto_increment |
| commons     | int(11)                                                              | YES  | MUL | NULL                |                |
| hash        | bigint(20) unsigned                                                  | YES  | MUL | NULL                |                |
| width       | int(11)                                                              | YES  |     | NULL                |                |
| height      | int(11)                                                              | YES  |     | NULL                |                |
| created     | timestamp                                                            | NO   |     | current_timestamp() |                |
| thumb_width | int(11)                                                              | YES  |     | NULL                |                |
| thumb_type  | enum('default','error','lossy-page1','lossy-page2','lossless-page1') | YES  |     | NULL                |                |
+-------------+----------------------------------------------------------------------+------+-----+---------------------+----------------+
8 rows in set (0.001 sec)

describe status;
+------------------------+--------------+------+-----+---------+-------+
| Field                  | Type         | Null | Key | Default | Extra |
+------------------------+--------------+------+-----+---------+-------+
| keyword                | varchar(255) | NO   | PRI | NULL    |       |
| last_processed_page_id | bigint(20)   | YES  |     | NULL    |       |
+------------------------+--------------+------+-----+---------+-------+
2 rows in set (0.002 sec)
```

### Querying the hashes in Mariadb

Query for finding duplicates for images defined by page_id. The maximum difference is an integer representing how many bits can be different when comparing hashes. Smaller value means less difference. Ie. 1 = no difference. 10 = huge difference.

```
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
```




