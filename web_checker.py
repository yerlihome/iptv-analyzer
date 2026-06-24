import streamlit as st
import requests
from datetime import datetime
import concurrent.futures

st.set_page_config(page_title="Pro IPTV Analyzer", page_icon="📺", layout="wide")

# CSS ile Görsel Özelleştirme
st.markdown("""
<style>
    .reportview-container { background: #f0f2f6; }
    .stButton>button { width: 100%; background-color: #4CAF50; color: white; font-weight: bold; }
    .success-card { padding: 15px; border-radius: 5px; border-left: 5px solid #28a745; background-color: #e8f5e9; margin-bottom: 10px; color: #1b5e20; }
    .fail-card { padding: 10px; border-radius: 5px; border-left: 5px solid #dc3545; background-color: #fce8e6; margin-bottom: 10px; color: #c62828; }
</style>
""", unsafe_allow_html=True)

st.title("🚀 Pro IPTV Çoklu Format Tarayıcı & Analizör")
st.write("M3U, TXT veya Xtream Panellerini yükleyin. Sistem çökmelere karşı tamamen izole edilmiştir.")

# Sol Panel Ayarları
st.sidebar.header("⚙️ Gelişmiş Ayarlar")
threads = st.sidebar.slider("Tarama Hızı (Eşzamanlı İstek)", 5, 50, 15)
timeout = st.sidebar.slider("Zaman Aşımı (Saniye)", 1, 15, 5)

input_type = st.radio("Giriş Yöntemi:", ["Metin Olarak Yapıştır", "Dosya Yükle (.txt / .m3u)"])

raw_lines = []
if input_type == "Metin Olarak Yapıştır":
    raw_text = st.text_area("IPTV Verilerini Giriş Yapın:", height=200, placeholder="Linkleri buraya yapıştırın...")
    if raw_text:
        raw_lines = raw_text.split("\n")
else:
    uploaded_file = st.file_uploader("Listenizi Seçin", type=["txt", "m3u"])
    if uploaded_file is not None:
        try:
            raw_lines = [line.decode("utf-8", errors="ignore").strip() for line in uploaded_file]
        except Exception as e:
            st.error(f"Dosya okunurken bir hata oluştu: {str(e)}")

def analyze_iptv(url):
    url = url.strip()
    if not url or not url.startswith("http"):
        return None
        
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    result = {
        "url": url, "status": "FAIL", "type": "Düz Link/M3U8",
        "exp_date": "N/A", "max_cap": "N/A", "active": "N/A"
    }

    # Format Tespiti (Xtream Panel mi?)
    is_xtream = "username=" in url or "user=" in url
    
    if is_xtream:
        result["type"] = "Xtream Panel"
        try:
            parts = url.split('/')
            base_url = f"{parts[0]}//{parts[2]}"
            username, password = "",""
            
            if "?" in url:
                params = url.split("?")[1].split("&")
                for param in params:
                    if "=" in param:
                        k, v = param.split("=", 1)
                        if k.lower() in ["username", "user"]: username = v
                        elif k.lower() in ["password", "pass"]: password = v
            
            if username and password:
                api_url = f"{base_url}/player_api.php?username={username}&password={password}"
                response = requests.get(api_url, headers=headers, timeout=timeout)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if isinstance(data, dict):
                            user_info = data.get("user_info", {})
                            if user_info and user_info.get("auth") == 1:
                                result["status"] = "OK"
                                exp = user_info.get("exp_date")
                                if exp in [None, "null", "", "0", 0]:
                                    result["exp_date"] = "Sınırsız / Ömürlük"
                                else:
                                    try:
                                        result["exp_date"] = datetime.fromtimestamp(int(exp)).strftime('%Y-%m-%d %H:%M')
                                    except:
                                        result["exp_date"] = "Belirsiz Format"
                                result["max_cap"] = str(user_info.get("max_connections", "1"))
                                result["active"] = str(user_info.get("active_cons", "0"))
                                result["url"] = f"{base_url}/get.php?username={username}&password={password}&output=ts"
                                return result
                    except Exception:
                        pass
        except Exception:
            pass

    # Genel HTTP Kontrolü (Düz M3U8, TS yayınları için)
    try:
        response = requests.get(url, headers=headers, timeout=timeout, stream=True)
        if response.status_code in [200, 206, 301, 302]:
            result["status"] = "OK"
            result["exp_date"] = "Canlı Yayın (Süresiz)"
            result["max_cap"] = "Sınırsız"
            result["active"] = "Bilinmiyor"
            return result
    except Exception:
        pass
        
    return result

if st.button("🚀 Kapsamlı Taramayı Başlat") and raw_lines:
    clean_urls = []
    for line in raw_lines:
        line_str = line.strip()
        if "http://" in line_str or "https://" in line_str:
            start_idx = line_str.find("http")
            potential_url = line_str[start_idx:].split(" ")[0].split('"')[0].split("'")[0]
            if potential_url not in clean_urls:
                clean_urls.append(potential_url)
    
    if not clean_urls:
        st.warning("Girişte veya dosyada 'http' ile başlayan geçerli bir link bulunamadı. Lütfen yapıştırdığınız metinde 'http://' ifadesinin yer aldığından emin olun.")
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        working_list = []
        broken_list = []
        total = len(clean_urls)
        
        col_ok, col_fail = st.columns(2)
        
        with col_ok:
            st.subheader("🟢 Çalışan Linkler")
            ok_placeholder = st.empty()
        with col_fail:
            st.subheader("🔴 Çalışmayan Linkler")
            fail_placeholder = st.empty()

        ok_html = ""
        fail_html = ""

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
                futures = [executor.submit(analyze_iptv, url) for url in clean_urls]
                
                for i, future in enumerate(concurrent.futures.as_completed(futures)):
                    try:
                        res = future.result()
                        if res:
                            if res["status"] == "OK":
                                working_list.append(res["url"])
                                ok_html += f"""<div class='success-card'>
                                    <b>🔗 Link:</b> {res['url']}<br>
                                    <b>📦 Format:</b> {res['type']} | ⏳ <b>Bitiş:</b> {res['exp_date']} | 👥 <b>Kapasite:</b> {res['max_cap']} Kişi (Aktif: {res['active']})
                                </div>"""
                                ok_placeholder.markdown(ok_html, unsafe_allow_html=True)
                            else:
                                broken_list.append(res["url"])
                                fail_html += f"<div class='fail-card'>❌ <b>Çalışmıyor:</b> {res['url']}</div>"
                                fail_placeholder.markdown(fail_html, unsafe_allow_html=True)
                    except Exception:
                        pass
                    
                    progress = (i + 1) / total
                    progress_bar.progress(progress)
                    status_text.text(f"İşleniyor: {i+1}/{total} (Başarılı: {len(working_list)} / Başarısız: {len(broken_list)})")
        except Exception as queue_error:
            st.error(f"Kritik işlem hatası engellendi: {str(queue_error)}")
            
        st.success("🎉 Tarama işlemi bitti!")
        
        # Sonuç İndirme Bölümü
        st.write("---")
        st.subheader("💾 Sonuçları Aktar")
        if working_list:
            output_data = "\n".join(working_list)
            st.download_button(
                label="📥 Çalışan Linkleri M3U/TXT Olarak İndir",
                data=output_data,
                file_name="calisan_iptv_listesi.txt",
                mime="text/plain"
            )
        else:
            st.error("İndirilecek aktif/çalışan bir link bulunamadı.")