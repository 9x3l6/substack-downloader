#!/usr/bin/env python3

# python3 -m venv .venv
# . .venv/bin/activate
# pip3 install feedparser requests markdownify pillow gazpacho
# ./ssdl.py https://karenkingston.substack.com/feed ~/Downloads/karenkingston

import os
import argparse
import feedparser
import requests
import markdownify
from PIL import Image
from gazpacho import Soup

def create_dir(directory):
    if not os.path.isdir(directory):
        if os.path.exists(directory):
            raise ValueError('Path exists: %s' % directory)
        else:
            os.makedirs(directory)

def fetch_feed(url):
    if '/feed' in url:
        rss_url = url
    else:
        rss_url = "%s/feed" % url

    rss = feedparser.parse(rss_url)
    return rss.entries

def fetch_and_parse(url):
    entries = fetch_feed(url)
    items = []
    for item in entries:
        title = item.title
        summary = item.summary
        link = item.link
        thumb = ''
        for l in item.links:
            if 'image/' in l.type:
                thumb = l.href
        pub_date = item.published
        html = item.content[0].value
        md = html2md(html)
        soup = Soup(html)
        images = soup.find('img')
        items.append({
            "title": title,
            "link": link,
            "thumb": thumb,
            "md": md,
            "images": images,
            "date": pub_date,
        })
    return items

def html2md(html):
    return markdownify.markdownify(html)

def save_files(directory, items):
    for item in items:
        print(item['title'])
        file_path = os.path.basename(item['link'])
        with open('%s%s%s.md' % (directory, os.path.sep, file_path), 'w') as file:
            file.write(item['md'])
        save_article_thumb(directory, item)
        save_article_images(directory, item)

def save_image(url, file_path):
    if url:
        data = requests.get(url).content
        ext = os.path.splitext(url)[1]
        if ext:
            with open('%s%s' % (file_path, ext), 'wb') as file:
                file.write(data)

def save_article_thumb(directory, item):
    url = item['thumb']
    if url:
        file_path = '%s%s%s' % (directory, os.path.sep, os.path.basename(item['link']))
        save_image(url, file_path)

def save_article_images(directory, item):
    def download_image(url):
        if url:
            ext = os.path.splitext(url)[1]
            file_path = '%s%s%s%s%s' % (directory, os.path.sep, os.path.basename(item['link']), os.path.sep, os.path.basename(url).replace(ext, ''))
            d = os.path.dirname(file_path)
            if not os.path.isdir(d):
                os.makedirs(d)
            save_image(url, file_path)
    if item['images']:
        if type(item['images']) == list:
            [download_image(img.attrs['src']) for img in item['images']]
        else:
            download_image(item['images'].attrs['src'])

def arguments():
    parser = argparse.ArgumentParser(description='Substack Downloader')
    parser.add_argument('url', help='Substack URL to download')
    parser.add_argument('dir', help='Directory where to download')

    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = arguments()
    create_dir(args.dir)
    articles = fetch_and_parse(args.url)
    save_files(args.dir, articles)
