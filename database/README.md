Backup db
- Warning: Expected size is 1.5GB
# mysqldump --defaults-file=~/replica.my.cnf --host=tools.db.svc.wikimedia.cloud s55462__imagehash |gzip > ~/imagehashdb-$(date -I).sql.gz

Backup schema
# mysqldump --defaults-file=~/replica.my.cnf --host=tools.db.svc.wikimedia.cloud --no-data s55462__imagehash > ~/imagehashdb-schema-$(date -I).sql

