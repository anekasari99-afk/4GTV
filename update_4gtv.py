import datetime
import subprocess
import time
from playwright.sync_api import sync_playwright

# Pemetaan lengkap ke-13 saluran (Hinet, Mozai, & VOD)
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
    "mozai_ftv_variety": "https://www.4gtv.tv/channel/4gtv-4gtv004?set=4&ch=16",  # FTV Variety
    "mozai_chuko": "https://www.4gtv.tv/channel/4gtv-4gtv006?set=4&ch=113",     # Chu Ko Liang
    "mozai_pts_drama": "https://www.4gtv.tv/channel/litv-ftv13?set=4&ch=31",     # PTS Drama
    "mozai_ftv_drama": "https://www.4gtv.tv/channel/litv-ftv09?set=4&ch=24",     # FTV Drama
    "vod_4gtv": "https://www.4gtv.tv/channel/fast-live241?set=4&ch=460"              # FastTV Variety
}

# Pemetaan unik untuk mencocokkan baris EXTINF di dalam file M3U
CHANNEL_IDENTIFIERS = {
    "4gtv-4gtv003": "民視第一台",
    "4gtv-4gtv001": "民視台灣台",
    "4gtv-4gtv002": "民視",
    "litv-ftv13": "民視新聞台",
    "litv-ftv07": "民視旅遊台",
    "4gtv-live021": "經典電影台",
    "4gtv-4gtv080": "原住民族電視台",
    "4gtv-4gtv079": "Arrirang",
    "mozai_ftv_variety": "民視綜藝台",
    "mozai_chuko": "豬哥亮歌廳秀",
    "mozai_pts_drama": "公視戲劇",
    "mozai_ftv_drama": "民視影劇台",
    "vod_4gtv": "FastTV Variety"
}

def update_git_repo():
    """Fungsi untuk otomatis add, commit, dan push file m3u ke GitHub"""
    try:
        subprocess.run(["git", "config", "--global", "user.name", "GitHub Actions Bot"], check=True)
        subprocess.run(["git", "config", "--global", "user.email", "actions@github.com"], check=True)
        
        subprocess.run(["git", "add", "taiwan_4gtv.m3u"], check=True)
        
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True)
        if not status.stdout.strip():
            print("[INFO] Tidak ada perubahan token baru pada file m3u.")
            return

        current_time = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        commit_msg = f"Auto-update 4GTV tokens: {current_time}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        subprocess.run(["git", "push"], check=True)
        print("[SUKSES] Semua token saluran valid berhasil diperbarui dan di-push ke GitHub!")
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
        browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        for key, web_url in CHANNELS_MAP.items():
            print(f"[INFO] Mengakses web untuk {key} -> {web_url}")
            current_captured_url = None

            def handle_req(request):
                nonlocal current_captured_url
                req_url = request.url
                # HANYA tangkap jika formatnya .m3u8 DAN mengandung parameter token & expires yang sah
                if ".m3u8" in req_url and "token=" in req_url and ("hinet.net" in req_url or "4gtv.tv" in req_url):
                    current_captured_url = req_url

            page.on("request", handle_req)

            try:
                page.goto(web_url, timeout=40000)
                time.sleep(6)
                try:
                    # Simulasi klik untuk memicu pemutar video men-generate token stream aktif
                    page.click("video, .jw-display-icon-container, .vjs-big-play-button", timeout=3000)
                except:
                    pass
                time.sleep(5)

                if current_captured_url:
                    captured_urls[key] = current_captured_url
                    print(f"[DAPAT] Token valid untuk {key}")
                else:
                    print(f"[PERINGATAN] Tidak ada stream ber-token tertangkap untuk {key}")
            except Exception as e:
                print(f"[ERROR] Gagal memuat halaman {web_url}: {e}")

            page.remove_listener("request", handle_req)

        browser.close()

    if captured_urls:
        print(f"[INFO] Berhasil menangkap {len(captured_urls)} token valid.")
        
        lines = content.splitlines()
        new_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            new_lines.append(line)
            
            if line.startswith("#EXTINF"):
                matched_key = None
                for key, identifier in CHANNEL_IDENTIFIERS.items():
                    if identifier in line:
                        matched_key = key
                        break
                
                if matched_key and matched_key in captured_urls:
                    if i + 1 < len(lines) and not lines[i + 1].startswith("#"):
                        new_lines.append(captured_urls[matched_key])
                        i += 2  # Lewati baris URL lama
                        continue
            i += 1

        content = "\n".join(new_lines)

        # Update timestamp baris kedua
        timestamp_str = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        content = re.sub(r'# Last Auto-Update:.*', f'# Last Auto-Update: {timestamp_str}', content)

        with open("taiwan_4gtv.m3u", "w", encoding="utf-8") as f:
            f.write(content)

        update_git_repo()
    else:
        print("[PERINGATAN] Tidak ada token baru yang tertangkap.")

if __name__ == "__main__":
    scrape_4gtv_tokens()
