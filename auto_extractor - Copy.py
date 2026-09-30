import time
import subprocess
import re
from playwright.sync_api import sync_playwright

# Pemetaan lengkap ke-13 saluran (Hinet, Mozai, & VOD)
# Pastikan URL web disesuaikan jika ada halaman khusus di 4GTV
CHANNELS_MAP = {
    "4gtv-4gtv003": "https://www.4gtv.tv/channel/4gtv-4gtv003?set=1&ch=1",  # FTV CH 1
    "4gtv-4gtv001": "https://www.4gtv.tv/channel/4gtv-4gtv001?set=1&ch=2",  # FTV Taiwan
    "4gtv-4gtv002": "https://www.4gtv.tv/channel/4gtv-4gtv002?set=1&ch=3",  # FTV
    "litv-ftv13": "https://www.4gtv.tv/channel/litv-ftv13?set=1&ch=31",  # FTV News
    "litv-ftv07": "https://www.4gtv.tv/channel/litv-ftv07?set=4&ch=61",  # FTV Travel
    "4gtv-live021": "https://www.4gtv.tv/channel/4gtv-live021",  # classic movie
    "4gtv-4gtv080": "https://www.4gtv.tv/channel/4gtv-4gtv080?set=4&ch=124",  # Indigenous
    "4gtv-4gtv079": "https://www.4gtv.tv/channel/4gtv-4gtv079?set=4&ch=189",  # Arrirang
    # Saluran Mozai & VOD
    "mozai_ftv_variety": "https://www.4gtv.tv/channel/4gtv-4gtv004?set=4&ch=16", # FTV Variety
    "mozai_chuko": "https://www.4gtv.tv/channel/4gtv-4gtv006?set=4&ch=113",     # Chu Ko Liang
    "mozai_pts_drama": "https://www.4gtv.tv/channel/litv-ftv13?set=4&ch=31",     # PTS Drama
    "mozai_ftv_drama": "https://www.4gtv.tv/channel/litv-ftv09?set=4&ch=24",     # FTV Drama
    "vod_4gtv": "https://www.4gtv.tv/channel/fast-live241?set=4&ch=460"              # FastTV Variety
}

def update_git_repo():
    """Fungsi untuk otomatis add, commit, dan push file m3u ke GitHub"""
    try:
        subprocess.run(["git", "add", "taiwan_4gtv.m3u"], check=True)
        subprocess.run(["git", "commit", "-m", "Auto-update all 13 4GTV tokens via local extractor"], check=True)
        subprocess.run(["git", "push"], check=True)
        print("[SUKSES] Semua token ke-13 saluran berhasil diperbarui dan di-push ke GitHub!")
    except Exception as e:
        print(f"[GAGAL PUSH] Terjadi kesalahan saat git push: {e}")

def scrape_4gtv_tokens():
    print("[INFO] Membaca daftar saluran dari file taiwan_4gtv.m3u...")
    try:
        with open("taiwan_4gtv.m3u", "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"[ERROR] Gagal membaca file m3u: {e}")
        return

    captured_urls = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        def handle_request(request):
            req_url = request.url
            if ".m3u8" in req_url and ("hinet.net" in req_url or "4gtv.tv" in req_url):
                # Deteksi otomatis kategori pool atau domain
                for key in CHANNELS_MAP.keys():
                    if key in req_url or (key.startswith("mozai") and "mozai" in req_url) or (key == "vod_4gtv" and "vod_4gtv" in req_url):
                        captured_urls[key] = req_url
                        print(f"[DAPAT] Token untuk kategori: {key}")

        page.on("request", handle_request)

        # Looping mengunjungi ke-13 web saluran satu per satu
        for key, web_url in CHANNELS_MAP.items():
            print(f"[INFO] Mengakses web untuk {key} -> {web_url}")
            try:
                page.goto(web_url, timeout=40000)
                time.sleep(5)
                try:
                    # Simulasi klik pemutar video
                    page.click("video, .jw-display-icon-container, .vjs-big-play-button", timeout=3000)
                except:
                    pass
                time.sleep(5)
            except Exception as e:
                print(f"[ERROR] Gagal memuat halaman {web_url}: {e}")

        browser.close()

    if captured_urls:
        print(f"[INFO] Berhasil menangkap {len(captured_urls)} token baru.")
        
        # Perbarui baris di dalam file m3u berdasarkan pola atau kata kunci saluran
        for key, new_url in captured_urls.items():
            if "mozai" in key:
                content = re.sub(r'(https://[^\s]+mozai[^\s]+)', new_url, content)
            elif key == "vod_4gtv":
                content = re.sub(r'(https://[^\s]+vod_4gtv[^\s]+)', new_url, content)
            else:
                pattern = rf"https://[^\s]+{key}[^\s]+"
                content = re.sub(pattern, new_url, content)

        with open("taiwan_4gtv.m3u", "w", encoding="utf-8") as f:
            f.write(content)

        update_git_repo()
    else:
        print("[PERINGATAN] Tidak ada token baru yang tertangkap.")

if __name__ == "__main__":
    scrape_4gtv_tokens()