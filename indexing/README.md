Toolforge Imagehash web API 

### Running standalone

```
# python -m venv venv
# source venv/bin/activate
# pip install --upgrade pip
# pip install -r requirements.txt
# python insert_phash_and_dhash_rc_v1el2_kubernetes.py
# deactivate
```

### Running in kubernetes
- https://wikitech.wikimedia.org/wiki/Help:Toolforge/Jobs_framework

Start job
```
# toolforge jobs run imagehashrc  --command "./t/run_imagehash6.sh" --image python3.11 --cpu 1  --mem 4Gi --wait
```
Showing info of job
```
# toolforge jobs show imagehashrc
```
Stopping kubernetes
```
#  toolforge jobs delete imagehashrc
```
Listing running jobs
```
# toolforge jobs list
```
Showing quota
```
# toolforge jobs quota
```
Logfiles
```
tail ~/imagehashrc.err
tail ~/imagehashrc.out
```
