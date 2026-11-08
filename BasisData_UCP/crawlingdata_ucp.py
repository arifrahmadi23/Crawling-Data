import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
import random
import time
from datetime import datetime
import re

# Koneksi ke MongoDB Atlas
client = MongoClient("mongodb+srv://arifrahmadi23:!!!Rahmadi23@arif.f3q1m.mongodb.net/?retryWrites=true&w=majority&appName=Arif")

def crawl_cnbc_keyword():
    base_url = 'https://www.cnbcindonesia.com/search?query=environmental+sustainability'
    collection = client['Environtmental_Sustainability']['Environment_Sustain']

    max_page = 10
    page = 1

    while page <= max_page:
        url = f'{base_url}&page={page}'
        print(f'Crawling halaman {page} -> {url}')

        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(res.text, 'lxml')

        articles = soup.find_all('article')
        if not articles:
            print('Tidak ada lagi artikel, proses crawling selesai.')
            break

        for artikel in articles:
            try:
                link_tag = artikel.find('a', href=True)
                link = link_tag['href'] if link_tag else None
                if not link:
                    print('Link tidak ditemukan.')
                    continue
                if not link.startswith('http'):
                    link = 'https:' + link

                judul_tag = artikel.find('h2') or artikel.find('h3')
                judul = judul_tag.text.strip() if judul_tag else None
                if not judul:
                    print('Judul tidak ditemukan.')
                    continue

                # Cek duplikat berdasarkan link atau judul
                if collection.find_one({'link': link}) or collection.find_one({'judul': judul}):
                    print(f'Artikel sudah ada: {judul[:50]}...')
                    continue

                isi_res = requests.get(link, headers={'User-Agent': 'Mozilla/5.0'})
                isi_soup = BeautifulSoup(isi_res.text, 'lxml')

                # Tanggal publish (bertingkat)
                tanggal = 'Tanggal tidak ditemukan'
                tanggal_meta = isi_soup.find('meta', {'property': 'article:published_time'})
                if tanggal_meta and tanggal_meta.get('content'):
                    tanggal = tanggal_meta['content'].strip()
                else:
                    # Coba cari elemen lain
                    tanggal_tag = isi_soup.find('div', class_='date') or isi_soup.find('span', class_='date')
                    if tanggal_tag:
                        tanggal = tanggal_tag.text.strip()
                    else:
                        # Coba ambil dari URL
                        match = re.search(r'/news/(\d{8})', link)
                        if match:
                            raw_date = match.group(1)  # contoh: '20240401'
                            tanggal = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:]}"
                        else:
                            # Fallback terakhir: tanggal saat ini
                            tanggal = datetime.now().strftime('%Y-%m-%d')

                # Author
                author_tag = isi_soup.find('div', class_='author')
                if author_tag:
                    author = author_tag.text.strip().replace('CNBC Indonesia,', '')
                else:
                    author_meta = isi_soup.find('meta', {'name': 'author'})
                    author = author_meta['content'].strip() if author_meta else 'Tidak tersedia'

                # Kategori / tag
                tags = 'Kategori tidak ditemukan'
                kategori_meta = isi_soup.find('meta', {'property': 'article:section'})
                if kategori_meta and kategori_meta.get('content'):
                    tags = kategori_meta['content'].strip()
                else:
                    # Fallback dari URL
                    parts = link.split('/')
                    if len(parts) > 3:
                        tags = parts[3]

                # Isi berita
                body_content = isi_soup.find('div', class_='detail_text')
                if body_content:
                    isi_paragraf_list = [
                        p.get_text(strip=True) for p in body_content.find_all('p') if p.get_text(strip=True)
                    ]
                    isi_berita = ' '.join(isi_paragraf_list) if isi_paragraf_list else 'Isi berita tidak ditemukan'
                else:
                    fallback_paragraf = isi_soup.find_all('p')
                    isi_paragraf_list = [
                        p.get_text(strip=True) for p in fallback_paragraf if p.get_text(strip=True)
                    ]
                    isi_berita = ' '.join(isi_paragraf_list) if isi_paragraf_list else 'Isi berita tidak ditemukan'

                # Thumbnail
                thumbnail_meta = isi_soup.find('meta', property='og:image')
                thumbnail_url = thumbnail_meta['content'].strip() if thumbnail_meta else 'Thumbnail tidak ditemukan'

                # Simpan ke MongoDB
                collection.insert_one({
                    'judul': judul,
                    'tanggal': tanggal,
                    'author': author,
                    'tags': tags,
                    'link': link,
                    'isi_berita': isi_berita,
                    'thumbnail': thumbnail_url
                })
                print(f'Simpan: {judul[:50]}...')

                # Delay untuk menghindari rate-limit
                time.sleep(random.uniform(0.5, 1.0))

            except Exception as e:
                print(f'Error saat proses artikel: {e}')

        page += 1

# Jalankan crawler
crawl_cnbc_keyword()