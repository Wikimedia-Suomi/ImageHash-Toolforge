# ImageHash-Toolforge
Tool uses image hashing to detect if image already exists in Wikimedia Commons. 

#### Status 7.9.2023
Phash and dhash index size is 14M photos of 85M photos in Wikimedia Commons. The index covers jpg, tiff webp images from Flickr, Finna, Europeana, and most of the photos from Nordic and Baltic countries. 

### Directories

- [web](./web) -- web API code, made with Flask, Vue, imagehash, Toolforge
- [indexing](./indexing) -- batchjob indexing code (pywikibot, mariadb)
- [database](./database) -- database schema 

### References
- Perceptual hashing ([pHashref](http://www.hackerfactor.com/blog/index.php?/archives/432-Looks-Like-It.html))
- Difference hashing ([dHashref](http://www.hackerfactor.com/blog/index.php?/archives/529-Kind-of-Like-That.html))
- [Imagehash library](https://github.com/JohannesBuchner/imagehash)  (Python)

### Usage

dhash+phash Search
- phash and dhash are calculated using Python Imagehash library.
- Both parameters are required.
- https://imagehash.toolforge.org/search?dhash=994677375445601741&phash=16302499845690113328

Page ID search
- Image hashes to be compared are fetched using page_id instead of getting them as parameters.
- It only works with images that are already indexed.
- The provided image is included in the result list.
- https://imagehash.toolforge.org/pagesearch?page_id=74155612

Page title search
- It is the same as page id search but uses page titles instead of page_id.
- https://imagehash.toolforge.org/pagesearch?page_title=Lehtojärvi_puinen_hirvenpääveistos.jpg

Finna id search
- Web page fetches thumbnail image from Finna.
- Calculate the phash and dhash values for the thumbnail.
- Then, it does dhash+phash search using calculated values.
- https://imagehash.toolforge.org/finnasearch?finna_id=musketti.M012:HK7155:2867-94-3

External links search
- Script does a SQL search from Toolforge's [Commonswiki_p.externallinks](https://www.mediawiki.org/wiki/Manual:Externallinks_table) table.
- el_to_domain_index = domain in reversed order
- el_to_path = freetext search from file path part of url
- https://imagehash.toolforge.org/externallinks?el_to_domain_index=fi.finna&el_to_path=museovirasto.DCCAB48D57705BAA2ADD460616E764F6
