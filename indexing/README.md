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


