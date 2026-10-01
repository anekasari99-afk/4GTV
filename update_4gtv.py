import datetime
import urllib.request
import urllib.error

def fetch_and_update_playlist():
    # URL Raw GitHub file taiwan_4gtv.m3u Anda sendiri
    source_url = "https://raw.githubusercontent.com/anekasari99-afk/4GTV/main/taiwan_4gtv.m3u"
    
    current_time = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{current_time}] Memulai pembaruan playlist 4GTV...")

    try:
        req = urllib.request.Request(
            source_url, 
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        
        with urllib.request.urlopen(req, timeout=15) as response:
            content = response.read().decode('utf-8')
            
        if "#EXTM3U" in content:
            header_comment = f"# Last Auto-Update: {current_time}\n"
            
            if "# Last Auto-Update:" in content:
                lines = content.splitlines()
                new_lines = []
                for line in lines:
                    if line.startswith("# Last Auto-Update:"):
                        new_lines.append(header_comment.strip())
                    else:
                        new_lines.append(line)
                final_content = "\n".join(new_lines)
            else:
                final_content = content.replace("#EXTM3U", f"#EXTM3U\n{header_comment.strip()}")

            with open("taiwan_4gtv.m3u", "w", encoding="utf-8") as f:
                f.write(final_content.strip())
                
            print("Sukses: File taiwan_4gtv.m3u berhasil diperbarui!")
        else:
            print("Peringatan: Data yang diunduh tidak valid format M3U.")
            
    except urllib.error.URLError as e:
        print(f"Gagal mengambil data dari sumber: {e.reason}")
    except Exception as e:
        print(f"Terjadi kesalahan tak terduga: {str(e)}")

if __name__ == "__main__":
    fetch_and_update_playlist()
