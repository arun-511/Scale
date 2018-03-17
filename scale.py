from urllib.request import urlopen
from urllib.parse import urlencode
from argparse import ArgumentParser
from mutagen import id3, File
from datetime import datetime
from os import path, remove, chdir, makedirs, system, getcwd, mkdir
from sqlite3 import connect, Row
from shutil import copy
from json import loads
from sys import argv

from util import Resolve

client = "a3e059563d7fd3372b49b37f00a00bcf"
urls   = {
    'resolve' : 'https://api.soundcloud.com/resolve?{0}',
    'playlist': 'https://api.soundcloud.com/users/{0}/playlists?limit=200{1}',
    'track'   : 'https://api.soundcloud.com/tracks/{0}?{1}',
    'stream'  : 'https://api.soundcloud.com/tracks/{0}/stream?{1}',
    'download': 'https://api.soundcloud.com/tracks/{0}/download?{1}'
}
buflen = 1024 * 32

libfile = connect(".library")
libfile.row_factory = Row
library = libfile.cursor()
library.execute("create table if not exists library(id text, title text, album text, artist text, genre text, year text, len text, artwork text, link text, compile int default 0, holt int default 0)")

def fetch_url(url):
    data   = urlopen(urls['resolve'].format(urlencode({'url' : url, 'client_id' : client})))
    bundle = loads(data.read())
    
    if bundle['kind'] == 'track':
        
        relese = datetime.strptime(bundle['created_at'], '%Y/%m/%d %H:%M:%S %z')

        bundle['title']  = Resolve().title(bundle['title'], bundle['user']['username'])
        bundle['album']  = Resolve().album(bundle['title'], bundle['user']['username'])
        bundle['artist'] = Resolve().artist(bundle['user']['username'])
            
        bundle['year']   = relese.strftime('%Y')
        bundle['month']  = relese.strftime('%B')
        bundle['day']    = relese.strftime('%A')
        
        if perl.album:
            bundle['album'] = perl.album
        if perl.cover:
            bundle['artwork_url'] = perl.cover
        
        formalfile(bundle)
        
    if bundle['kind'] == 'playlist':
        
        for tracl in bundle['tracks']:
            
            relese  = datetime.strptime(tracl['created_at'], '%Y/%m/%d %H:%M:%S %z')
            
            tracl['title']  = Resolve().title(tracl['title'], tracl['user']['username'])
            tracl['album']  = Resolve().album(bundle['title'], bundle['user']['username'])
            tracl['artist'] = Resolve().artist(bundle['user']['username'])
            
            tracl['year']   = relese.strftime('%Y')
            tracl['month']  = relese.strftime('%B')
            tracl['day']    = relese.strftime('%A')
            
            if perl.album:
                tracl['album'] = perl.album
            if perl.cover:
                tracl['artwork_url'] = perl.cover
            
            formalfile(tracl)
            
            
def formalfile(bundle):
    library.execute("select count(*) as len from library where id=:id", bundle)
    if not library.fetchone()["len"]:
        library.execute("select count(*) as len from library lib where not exists (select * from library where len=lib.len + 1 and album=:album) and album=:album order by cast(len as integer) asc", bundle)
        if library.fetchone()["len"]:
            library.execute("select len + 1 as len from library lib where not exists (select * from library where len=lib.len + 1 and album=:album) and album=:album order by cast(len as integer) asc limit 1", bundle)
            bundle["len"] = library.fetchone()["len"]
            
        else:
            library.execute("select count(*) + 1 as len from library where album=:album", bundle)
            bundle["len"] = library.fetchone()["len"]
            
        print(str(bundle["len"]).rjust(2), "|", bundle["id"], "|", bundle["title"])
        library.execute("insert into library(id, title, album, artist, genre, year, len, artwork, link) values(:id, :title, :album, :artist, :genre, :year, :len, :artwork_url, :permalink_url)", bundle)


def compilefile():
    library.execute("select album from library where compile=0 and holt=0 group by album") 
    for album in library.fetchall():
        library.execute("select count(*) as len from library where album=:album", dict(album))

        lentracl = library.fetchone()["len"]
        if lentracl > 1:
            if not path.exists(album["album"]):
                mkdir(album["album"])
            chdir(album["album"])
            
        library.execute("select id, title, album, artist, genre, year, len, artwork, link from library where album=:album and compile=0 and holt=0 order by cast(len as integer)", dict(album))
        for tracl in library.fetchall():

            print(tracl['len'].rjust(2), "|", tracl['id'], "|", tracl['title'])

            downloadfile(tracl)
            compiletracl(tracl)
            library.execute("update library set compile=1 where id=:id", dict(tracl))

        system("termux-media-scan *.mp3")

        if lentracl > 1:
            chdir("..")


def downloadfile(tracl):
    with urlopen(urls['stream'].format(tracl['id'], urlencode({'client_id' : client}))) as rawfile:
        with open("%s.mp3" % tracl['id'], 'wb') as localfile:
            while True:
                bulen = rawfile.read(buflen)
                if not bulen:
                    break
                localfile.write(bulen)


def downloadcover(tracl):
    if tracl['artwork'].startswith("_"):
        with open("../.asset/%s.jpeg" % tracl['artwork'], 'rb') as rawfile:
            return rawfile.read()
    elif tracl['artwork']:
        with urlopen(tracl['artwork'].replace('large', 't500x500')) as rawfile:
            return rawfile.read()
    else:
        with open("cover_defult.jpeg", 'rb') as rawfile:
            return rawfile.read()


def compiletracl(tracl):
    rawfile = File("%s.mp3" % tracl['id'])
    
    rawfile['TIT2'] = id3.TIT2(encoding=3, text=tracl['title'])
    rawfile['TALB'] = id3.TALB(encoding=3, text=tracl['album'])
    rawfile['TPE1'] = id3.TPE1(encoding=3, text=tracl['artist'])
    rawfile['TCON'] = id3.TCON(encoding=3, text=tracl['genre'])
    rawfile['TYER'] = id3.TYER(encoding=3, text=tracl['year'])
    rawfile['TRCK'] = id3.TRCK(encoding=3, text=tracl['len'])
    rawfile['WOAS'] = id3.WOAS(encoding=3, text=tracl['link'])
    
    rawfile['APIC'] = id3.APIC(
                          encoding = 3,
                          type     = 3,
                          mime     = 'image/jpeg',
                          desc     = 'Cover',
                          data     = downloadcover(tracl)
                      )
    
    rawfile.save(v2_version=3)


def migratelib():
    #dose not work for now.
    pass

def relorder(**tracl):
    library.execute("update library set len=len+1 where len>:len and len<(select len from library where id=:id)", tracl)


perl = ArgumentParser()
perl.add_argument("-l",  default="", dest="url")
perl.add_argument("-al", default="", dest="album")
perl.add_argument("-tl", default="", dest="cover")
perl.add_argument("-migrate", action="store_true", dest="mig")
perl.add_argument("-compile", action="store_true", dest="com")
perl.add_argument("-version", action="store_true", dest="ver")
perl = perl.parse_args(argv[1:])

if perl.url:
    fetch_url(perl.url)
    

if perl.com:
    compilefile()
        

if perl.mig:
    migratelib()
   
   
if perl.ver:
    print("Scale 0.2.5")
        
libfile.commit()
libfile.close()