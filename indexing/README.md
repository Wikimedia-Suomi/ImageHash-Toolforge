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



