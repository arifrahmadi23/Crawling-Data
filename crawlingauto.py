import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
import random
import time

# Koneksi ke MongoDB Atlas
client = MongoClient("mongodb+srv://arifrahmadi23:!!!Rahmadi23@arif.f3q1m.mongodb.net/?retryWrites=true&w=majority&appName=Arif")

def crawl_detik_keyword():
  base_url = 'https://www.detik.com/search/searchall?query=real%20madrid%20vs%20barcelona'
  collection = client['Scheduler_auto']['Madrid_Barca']

  # Tentukan jumlah halaman yang ingin di-crawl
  max_page = 5
  page = 1
  while page <= max_page: # Mengganti kondisi while dengan pembatasan halaman
    url = f'{base_url}&page={page}&result_type=relevansi'
    print(f'Crawling halaman {page} -> {url}')

    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'lxml')

    articles = soup.find_all('article')
    if not articles:
      print ('Tidak ada lagi artikel, proses crawling selesai.')
      break

    for artikel in articles:
      try:
        link_tag = artikel.find('a')
        link = link_tag['href'] if link_tag else None
        if not link:
            print('Link artikel tidak ditemukan.')
            continue

        judul_tag = artikel.find('h3')
        judul = judul_tag.text.strip() if judul_tag else None
        if not judul:
            print('Judul artikel tidak ditemukan.')
            continue

        # Cel duplikat berdasarkan link atau judul
        if collection.find_one({'link': link}) or collection.find_one({'judul': judul}):
          print(f'Artikel sudah ada: {judul[:50]}...')
          continue

        isi_res = requests.get(link)
        isi_soup = BeautifulSoup(isi_res.text, 'lxml')

        # Meta info
        tanggal_meta = isi_soup.find('meta', attrs={'name': 'dtk:publishdate'})
        tanggal = tanggal_meta['content'].strip() if tanggal_meta else 'Tanggal tidak ditemukan'


        author_meta = isi_soup.find('meta', attrs={'name': 'dtk:author'})
        author = author_meta['content'].strip() if author_meta else 'Tidak tersedia'

        description_meta = isi_soup.find('meta', attrs={'name': 'description'})
        description = description_meta['content'].strip() if description_meta else 'Deskripsi tidak ditemukan'

        tags_meta = isi_soup.find('meta', attrs={'name': 'keywords'})
        tags = tags_meta['content'].strip() if tags_meta else ['Tags tidak ditemukan']

        # Ambil isi berita
        body_content = isi_soup.find('div', class_='detail__body-text itp_bodycontent')
        if body_content and body_content.get('id') != 'detikdetailtext':
          isi_paragraf_list = [p.get_text(strip=True) for p in body_content.find_all('p') if p.get_text(strip=True)]
          isi_berita = ' '.join(isi_paragraf_list) if isi_paragraf_list else 'Isi berita tidak ditemukan'
        else:
          fallback_paragraf = isi_soup.find_all('p')
          isi_paragraf_list = [p.get_text(strip=True) for p in fallback_paragraf if p.get_text(strip=True)]
          isi_berita = ' '.join(isi_paragraf_list) if isi_paragraf_list else 'Isi berita tidak ditemukan'

        # Ambil thumbnail
        thumbnail_meta = isi_soup.find('meta', attrs={'name': 'dtk:thumbnail'}) or isi_soup.find('meta', attrs={'property': 'og:image'})
        thumbnail_url = thumbnail_meta['content'].strip() if thumbnail_meta else 'Thumbnail tidak ditemukan'

        # Simpan ke MongoDB
        collection.insert_one({
            'judul': judul,
            'tanggal': tanggal,
            'author': author,
            'description': description,
            'tags': tags,
            'link': link,
            'isi_berita': isi_berita,
            'thumbnail': thumbnail_url
        })
        print(f' Simpan: {judul[:50]}...')

        time.sleep(random.uniform(0.1, 0.5))

      except Exception as e:
        print(f'Error saat proses artikel: {e}')

    page += 1

# Jalankan crawler
crawl_detik_keyword()






