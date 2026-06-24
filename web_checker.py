import streamlit as st
import requests
from datetime import datetime
import concurrent.futures
import re
from urllib.parse import urlparse, parse_qs
import time

st.set_page_config(page_title="ŞAHİN NEON MATRIX V11", page_icon="🦅", layout="wide")

# -------------------------------------------------------------
# TMDB API AYARLARI 
# -------------------------------------------------------------
TMDB_API_KEY = "59b28b762df3ac4682548eb29342557b" 

# -------------------------------------------------------------
# ARKA PLAN HAFIZA TANIMLAMALARI
# -------------------------------------------------------------
if "s2_status" not in st.session_state: st.session_state.s2_status = "Pasif"
if "s2_cap" not in st.session_state: st.session_state.s2_cap = "1 Panel Girişi"
if "s3_status" not in st.session_state: st.session_state.s3_status = "Pasif"
if "s3_cap" not in st.session_state: st.session_state.s3_cap = "Liste Yapıştırılmadı"
if "selected_actor_id" not in st.session_state: st.session_state.selected_actor_id = None
if "selected_actor_name" not in st.session_state: st.session_state.selected_actor_name = None
if "active_xtream_results" not in st.session_state: st.session_state.active_xtream_results = []

# -------------------------------------------------------------
# IPTV PORTAL & PREMIUM STREAMER UI TEMA CSS ENJEKSİYONU
# -------------------------------------------------------------
st.markdown("""
<style>
    /* Global Karanlık IPTV Teması */
    .stApp { background: linear-gradient(145deg, #070913 0%, #0f1123 100%) !important; color: #e2e8f0 !important; font-family: 'Segoe UI', sans-serif; }
    .stTabs [data-baseweb="tab-list"] { background-color: #0b0d19; border-radius: 14px; padding: 6px; border: 1px solid #1a1f3c; }
    .stTabs [data-baseweb="tab"] { color: #7e8ebc !important; font-weight: 600; padding: 12px 24px; border-radius: 10px; }
    .stTabs [aria-selected="true"] { color: #00ff66 !important; background-color: #161a35 !important; box-shadow: 0 0 15px rgba(0,255,102,0.15); }
    .stTextInput input, .stTextArea textarea { background-color: #060813 !important; color: #ffffff !important; border: 1px solid #1f2445 !important; border-radius: 10px !important; }
    
    /* Neon Matrix Butonları */
    .stButton>button { width: 100%; background: linear-gradient(90deg, #00ff66 0%, #00993d 100%) !important; color: #000000 !important; font-weight: 800 !important; letter-spacing: 0.5px; height: 42px; border: none !important; border-radius: 8px !important; transition: all 0.3s ease; }
    .stButton>button:hover { background: linear-gradient(90deg, #33ff85 0%, #00ff66 100%) !important; box-shadow: 0 0 20px rgba(0, 255, 102, 0.4); transform: translateY(-1px); }
    
    /* Aktör Kartı Butonu (IPTV Kanal Seçim Tarzı) */
    div[data-testid="stFormSubmitButton"]>button, .actor-gallery-card button { height: 26px !important; font-size: 11px !important; padding: 0 5px !important; background: #161a35 !important; color: #00ff66 !important; border: 1px solid #283163 !important; border-radius: 6px !important;}
    .actor-gallery-card button:hover { background: #00ff66 !important; color: #000 !important; box-shadow: 0 0 10px rgba(0,255,102,0.3); }

    /* IPTV Akış Kartları */
    .movie-card { background: rgba(11, 14, 28, 0.95); border: 1px solid #1c2242; border-radius: 16px; padding: 25px; margin-bottom: 25px; box-shadow: 0 15px 35px rgba(0,0,0,0.6); position: relative; overflow: hidden; }
    .movie-card::before { content: ''; position: absolute; top: 0; left: 0; width: 6px; height: 100%; background: #00ff66; }
    .movie-title { color: #ffffff !important; font-size: 28px !important; font-weight: 800; tracking: -0.5px; }
    
    /* IPTV Kanal Listesi Görünümlü Oyuncu Galerisi (Daire Formatı) */
    .actor-gallery-card { background: #090b14; border: 1px solid #181d36; border-radius: 14px; padding: 12px 6px; text-align: center; transition: all 0.3s ease; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
    .actor-gallery-card:hover { border-color: #00ff66; transform: scale(1.05); box-shadow: 0 0 20px rgba(0,255,102,0.2); }
    
    /* Yuvarlak Profil Avatar Düzeni */
    .actor-img-container { width: 75px; height: 75px; margin: 0 auto 8px auto; overflow: hidden; border-radius: 50%; border: 2px solid #1c2242; transition: all 0.3s ease; }
    .actor-gallery-card:hover .actor-img-container { border-color: #00ff66; }
    .actor-img-container img { width: 100%; height: 100%; object-fit: cover; filter: brightness(0.85); }
    .actor-gallery-card:hover img { filter: brightness(1.1); }

    /* Medya Player Bilgi Segmentleri */
    .section-title { color: #46a3ff; font-size: 13px; font-weight: 700; letter-spacing: 1px; margin-top: 22px; margin-bottom: 12px; border-bottom: 1px solid #1c2242; padding-bottom: 6px; text-transform: uppercase;}
    .rating-badge { background: #12162b; border: 1px solid #ffaa00; padding: 4px 10px; border-radius: 6px; color: #ffaa00; font-weight: bold; font-size: 13px; display: inline-block; }
    .neon-card { padding: 16px; border-radius: 12px; background: #0d101d; margin-bottom: 15px; border: 1px solid #1c2242; }
    .stat-box { background: #090b14; border: 1px solid #181d36; padding: 12px; border-radius: 10px; text-align: center; }
    .stat-label { font-size: 10px; color: #6977a1; letter-spacing: 0.5px; }
    .stat-value { font-size: 16px; font-weight: 700; color: #00ff66; margin-top: 2px; }

    /* Platform Linkleri */
    .platform-btn { display: flex; align-items: center; justify-content: center; gap: 8px; background: #13172d; border: 1px solid #222952; padding: 10px; border-radius: 8px; color: #cbd5e1 !important; text-decoration: none !important; font-weight: 600; font-size: 13px; transition: all 0.2s ease; margin-bottom: 10px;}
    .platform-btn:hover { background: #1c2242; border-color: #00ff66; color: #fff !important; transform: translateY(-1px); }
    .platform-btn img { width: 18px; height: 18px; object-fit: contain; }
</style>
""", unsafe_allow_html=True)

def render_status_dashboard(capacity_info="Beklemede", status="Pasif"):
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.markdown(f"<div class='stat-box'><div class='stat-label'>📅 SİSTEM TARİHİ</div><div class='stat-value'>{datetime.now().strftime('%d.%m.%Y')}</div></div>", unsafe_allow_html=True)
    with col2: st.markdown(f"<div class='stat-box'><div class='stat-label'>⏰ STREAM SAATİ</div><div class='stat-value'>{datetime.now().strftime('%H:%M:%S')}</div></div>", unsafe_allow_html=True)
    with col3: st.markdown(f"<div class='stat-box'><div class='stat-label'>📊 PLATFORM KAPASİTE</div><div class='stat-value'>{capacity_info}</div></div>", unsafe_allow_html=True)
    c = "#00ff66" if status == "Aktif" else "#ffaa00"
    with col4: st.markdown(f"<div class='stat-box'><div class='stat-label'>⚡ CORE ENGINE</div><div class='stat-value' style='color:{c};'>{status}</div></div>", unsafe_allow_html=True)
    st.write("---")

def parse_and_validate_xtream(url, timeout=4.0):
    try:
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        queries = parse_qs(parsed.query)
        username = queries.get('username', [''])[0]
        password = queries.get('password', [''])[0]
        
        if not username or not password:
            with requests.get(url, headers={'User-Agent': 'VLC/3.0.18'}, timeout=timeout, stream=True) as r:
                if r.status_code in [200, 206]:
                    return {"url": url, "type": "M3U_Stream", "status": "Aktif"}
            return None

        api_url = f"{base_url}/player_api.php?username={username}&password={password}"
        res = requests.get(api_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=timeout)
        if res.status_code == 200:
            data = res.json()
            u_info = data.get("user_info", {})
            exp_timestamp = u_info.get("exp_date")
            if exp_timestamp and exp_timestamp != "null" and str(exp_timestamp).isdigit():
                exp_date = datetime.fromtimestamp(int(exp_timestamp)).strftime('%d.%m.%Y')
            else:
                exp_date = "Süresiz"
                
            return {
                "url": url, "type": "Xtream_API", "status": u_info.get("status", "Active"),
                "max_connections": u_info.get("max_connections", "1"), "active_cons": u_info.get("active_cons", "0"),
                "exp_date": exp_date, "server": base_url, "username": username, "password": password
            }
    except: pass
    return None

def render_movie_card(movie_data, unique_suffix):
    title = movie_data.get("title", "Bilinmeyen Film")
    original_title = movie_data.get("original_title", title)
    overview = movie_data.get("overview", "Bu yapım için Türkçe özet veritabanında bulunamadı.")
    if not overview: overview = "Özet bilgisi mevcut değil."
    
    release_date = movie_data.get("release_date", "Bilinmiyor")
    year = release_date.split("-")[0] if "-" in release_date else "Bilinmiyor"
    runtime = movie_data.get("runtime", 0)
    vote_avg = round(movie_data.get("vote_average", 0), 1)
    poster_path = movie_data.get("poster_path")
    poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else "https://via.placeholder.com/500x750?text=Afi%C5%9F+Yok"
    
    st.markdown("<div class='movie-card'>", unsafe_allow_html=True)
    c_post, c_det = st.columns([1, 4])
    
    with c_post:
        st.image(poster_url, use_container_width=True)
        st.markdown(f"<div style='text-align:center;margin-top:10px;'><span class='rating-badge'>🌟 IMDb: {vote_avg}</span></div>", unsafe_allow_html=True)
    
    with c_det:
        st.markdown(f"<div class='movie-title'>{title} <span style='color:#6977a1; font-size:20px; font-weight:400;'>({year})</span></div>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#94a3b8; font-size:14px; line-height:1.6;'>{overview}</p>", unsafe_allow_html=True)
        st.markdown(f"<span style='font-size:12px; background:#1e293b; padding:4px 8px; border-radius:4px; color:#94a3b8;'>📅 {release_date}</span> &nbsp; <span style='font-size:12px; background:#1e293b; padding:4px 8px; border-radius:4px; color:#94a3b8;'>⏱️ {runtime} Dk</span>", unsafe_allow_html=True)
        
        slug = title.replace(" ", "+")
        orig_slug = original_title.replace(" ", "+")
        
        hd_direct = f"https://www.hdfilmcehennemi.life/?s={slug}"
        fm_direct = f"https://www.filmmodu.org/ara?q={slug}"
        ff_direct = f"https://www.fullhdfilmizlesene.de/arama/{slug}"
        
        download_1080p = f"https://www.google.com/search?q={orig_slug}+{year}+1080p+dual+bluray+indir"
        download_4k = f"https://www.google.com/search?q={orig_slug}+{year}+2160p+4k+dual+web-dl+indir"
        torrent_url = f"https://www.google.com/search?q={orig_slug}+{year}+1080p+bluray+torrent+download"
        
        g_url = f"https://www.google.com/search?q={slug}+nereden+izlenir"
        net_url = f"https://www.netflix.com/search?q={slug}"
        prm_url = f"https://www.amazon.com/s?k={slug}+movie"
        dis_url = f"https://www.disneyplus.com/search?q={slug}"
        apl_url = f"https://tv.apple.com/search?term={slug}"
        
        imdb_url = f"https://www.imdb.com/find?q={slug}"
        eksi_url = f"https://eksisozluk.com/goster.aspx?mantik=normal&kw={slug}"
        
        vids = movie_data.get("videos", {}).get("results", []) if isinstance(movie_data.get("videos"), dict) else []
        tr_url = next((f"https://www.youtube.com/watch?v={v['key']}" for v in vids if v.get("site") == "YouTube"), None)

        st.markdown("<div class='section-title'>🖥️ IPTV LİSANS / VOD OYNATICI PLATFORMLARI</div>", unsafe_allow_html=True)
        bg1, bg2, bg3, bg4, bg5 = st.columns(5)
        with bg1: st.markdown(f'<a class="platform-btn" href="{g_url}" target="_blank"><img src="https://www.google.com/favicon.ico">Google Stream</a>', unsafe_allow_html=True)
        with bg2: st.markdown(f'<a class="platform-btn" href="{net_url}" target="_blank"><img src="https://images.ctfassets.net/4cd45et68cgf/4nEB8vYLMwG96bCg4gZ3iE/1b1241ceb616b7da8461ac6c2aa95e86/Netflix-Brand-Logo.png">Netflix VOD</a>', unsafe_allow_html=True)
        with bg3: st.markdown(f'<a class="platform-btn" href="{prm_url}" target="_blank"><img src="https://www.amazon.com/favicon.ico">Prime Hub</a>', unsafe_allow_html=True)
        with bg4: st.markdown(f'<a class="platform-btn" href="{dis_url}" target="_blank"><img src="https://static-assets.bamgrid.com/product/disneyplus/images/favicon.ico.8f9b96c8104ecab81c3c3a9f0f970e44.ico">Disney+</a>', unsafe_allow_html=True)
        with bg5: st.markdown(f'<a class="platform-btn" href="{apl_url}" target="_blank"><img src="https://www.apple.com/favicon.ico">Apple TV+</a>', unsafe_allow_html=True)
        
        st.markdown("<div class='section-title'>🍿 INSTANT STREAM PLAYER KANALLARI (REDIRECTIONS)</div>", unsafe_allow_html=True)
        bf1, bf2, bf3, bf4, bf5 = st.columns(5)
        with bf1: st.markdown(f'<a class="platform-btn" style="border-color:#ffbb33;" href="{hd_direct}" target="_blank"><img src="https://www.hdfilmcehennemi.life/favicon.ico">HDFilmCehennemi</a>', unsafe_allow_html=True)
        with bf2: st.markdown(f'<a class="platform-btn" style="border-color:#00c851;" href="{fm_direct}" target="_blank"><img src="https://www.filmmodu.org/favicon.ico">FilmModu Portal</a>', unsafe_allow_html=True)
        with bf3: st.markdown(f'<a class="platform-btn" style="border-color:#33b5e5;" href="{ff_direct}" target="_blank"><img src="https://www.fullhdfilmizlesene.de/arama/{slug}">FullHD İzle</a>', unsafe_allow_html=True)
        with bf4: st.markdown(f'<a class="platform-btn" href="{torrent_url}" target="_blank"><img src="https://www.bittorrent.com/favicon.ico">Torrent Engine</a>', unsafe_allow_html=True)
        with bf5: st.markdown(f'<a class="platform-btn" href="https://www.turkcealtyazi.org/find.php?find={slug}" target="_blank"><img src="https://www.turkcealtyazi.org/favicon.ico">Subtitles (TA)</a>', unsafe_allow_html=True)

        st.markdown("<div class='section-title'>📥 DIRECT HIGH-SPEED DOWNLOAD NODES</div>", unsafe_allow_html=True)
        bd1, bd2 = st.columns(2)
        with bd1: st.markdown(f'<a class="platform-btn" style="border-color:#a855f7; background:rgba(168,85,247,0.1);" href="{download_1080p}" target="_blank">📥 Download 1080p Full HD Dual (TR-EN)</a>', unsafe_allow_html=True)
        with bd2: st.markdown(f'<a class="platform-btn" style="border-color:#06b6d4; background:rgba(6,182,212,0.1);" href="{download_4k}" target="_blank">🚀 Download 4K Ultra HD Dual (TR-EN)</a>', unsafe_allow_html=True)

        st.markdown("<div class='section-title'>📊 META DATA & TRAILER FEED</div>", unsafe_allow_html=True)
        bx1, bx2, bx3 = st.columns(3)
        with bx1:
            if tr_url: st.markdown(f'<a class="platform-btn" style="background:#cc0000;color:#fff !important;border:none;" href="{tr_url}" target="_blank"><img src="https://www.youtube.com/favicon.ico">LIVE TRAILER WATCH</a>', unsafe_allow_html=True)
            else: st.markdown('<a class="platform-btn" style="opacity:0.4;pointer-events:none;">Trailer Offline</a>', unsafe_allow_html=True)
        with bx2: st.markdown(f'<a class="platform-btn" style="background:#f5c518;color:#000 !important;border:none;" href="{imdb_url}" target="_blank"><img src="https://m.media-amazon.com/images/G/01/imdb/images-ANDY/images/favicon_desktop_32x32._CB473688197_.png">IMDb Database</a>', unsafe_allow_html=True)
        with bx3: st.markdown(f'<a class="platform-btn" style="background:#009e49;color:#fff !important;border:none;" href="{eksi_url}" target="_blank"><img src="https://eksisozluk.com/favicon.ico">Ekşi Sözlük Feed</a>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🍿 ŞAHİN LIVE IPTV VOD", "🔮 MATRIX GRID SCANNER", "📺 XTREAM CONTROLLER"])

# -------------------------------------------------------------
# SEKME 1: ŞAHİN IPTV VOD PLATFORMU
# -------------------------------------------------------------
with tab1:
    st.title("🦅 Şahin Premium Media VOD Hub")
    render_status_dashboard("IPTV VOD Engine V12", "Aktif")
    
    movie_query = st.text_input("🔍 İzlemek istediğiniz Yapım, Aktör veya Sahne Sanatçısı Girin:", placeholder="Örn: Inception, Keanu Reeves, Brad Pitt...", key="movie_search_input")
    
    if movie_query.strip():
        person_search_url = f"https://api.themoviedb.org/3/search/person?api_key={TMDB_API_KEY}&query={movie_query}&language=tr-TR"
        
        try:
            person_response = requests.get(person_search_url, timeout=5)
            person_results = person_response.json().get("results", []) if person_response.status_code == 200 else []
            
            if person_results and person_results[0].get("popularity", 0) > 4.0:
                person = person_results[0]
                st.session_state.selected_actor_id = person.get("id")
                st.session_state.selected_actor_name = person.get("name")
            else:
                search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={movie_query}&language=tr-TR"
                response = requests.get(search_url, timeout=5)
                
                if response.status_code == 200:
                    results = response.json().get("results", [])
                    if results:
                        st.success(f"🎬 {len(results)} Medya Akışı Listelendi. IPTV Yapısı Hazırlanıyor...")
                        
                        for idx, movie in enumerate(results[:2]):  
                            m_id = movie.get("id")
                            det_url = f"https://api.themoviedb.org/3/movie/{m_id}?api_key={TMDB_API_KEY}&language=tr-TR&append_to_response=videos,credits"
                            
                            try:
                                det_res = requests.get(det_url, timeout=5)
                                details = det_res.json() if det_res.status_code == 200 else movie
                            except:
                                details = movie
                            
                            render_movie_card(details, f"direct_{m_id}_{idx}")
                            
                            # IPTV OYNATICI STİLİNDE KÜÇÜLTÜLMÜŞ YUVARLAK OYUNCU SEÇİM PANELİ
                            cast_list = details.get("credits", {}).get("cast", [])
                            if cast_list:
                                st.markdown("<div class='section-title'>🎭 CAST & ACTOR SELECTION PORTAL (KATALOGDAN SEÇ)</div>", unsafe_allow_html=True)
                                
                                # 8 Sütunlu Kompakt Mini Listeleme (IPTV Kanal Seçim Çemberleri)
                                actor_cols = st.columns(8)
                                for a_idx, actor in enumerate(cast_list[:8]):
                                    a_name = actor.get("name")
                                    a_id = actor.get("id")
                                    a_img = actor.get("profile_path")
                                    a_img_url = f"https://image.tmdb.org/t/p/w185{a_img}" if a_img else "https://via.placeholder.com/150x150?text=No+User"
                                    
                                    with actor_cols[a_idx]:
                                        st.markdown(f"<div class='actor-gallery-card'>", unsafe_allow_html=True)
                                        st.markdown("<div class='actor-img-container'>", unsafe_allow_html=True)
                                        st.image(a_img_url, use_container_width=True)
                                        st.markdown("</div>", unsafe_allow_html=True)
                                        st.markdown(f"<p style='font-size:10px; font-weight:700; color:#e2e8f0; height:15px; overflow:hidden; margin:2px 0 6px 0;'>{a_name}</p>", unsafe_allow_html=True)
                                        
                                        # Kesin Tıklama Çözümü Sunan IPTV Kanal Seçim Butonu
                                        if st.button("▶ Profil", key=f"act_btn_{m_id}_{a_id}_{a_idx}"):
                                            st.session_state.selected_actor_id = a_id
                                            st.session_state.selected_actor_name = a_name
                                            st.rerun()
                                        st.markdown("</div>", unsafe_allow_html=True)
                    else:
                        st.error("🔍 IPTV Veritabanında eşleşen medya veya aktör kaydı bulunamadı.")
        except Exception as e:
            st.error(f"Siber Katman Bağlantı Hatası: {str(e)}")

    # OYUNCU DETAY MATRIX FEED (Tıklanınca sayfa altında açılan listeleme)
    if st.session_state.selected_actor_id:
        st.write("---")
        st.markdown(f"<div style='background:rgba(0,255,102,0.05); padding:15px; border-radius:12px; border:1px solid rgba(0,255,102,0.2); margin-bottom:20px;'><h3 style='color:#00ff66; margin:0;'>📺 MEDIA PLAYER MATRIX FEED: {st.session_state.selected_actor_name}</h3><p style='color:#6977a1; font-size:12px; margin:5px 0 0 0;'>Seçilen aktörün yer aldığı tüm aktif IPTV/VOD kanalları ve dijital platform akışları aşağıda listelenmiştir.</p></div>", unsafe_allow_html=True)
        
        credits_url = f"https://api.themoviedb.org/3/person/{st.session_state.selected_actor_id}/movie_credits?api_key={TMDB_API_KEY}&language=tr-TR"
        try:
            c_res = requests.get(credits_url, timeout=5)
            if c_res.status_code == 200:
                cast_movies = c_res.json().get("cast", [])
                cast_movies = sorted(cast_movies, key=lambda x: x.get("popularity", 0), reverse=True)
                
                if cast_movies:
                    for idx, m_credit in enumerate(cast_movies[:6]):
                        m_id = m_credit.get("id")
                        full_movie_url = f"https://api.themoviedb.org/3/movie/{m_id}?api_key={TMDB_API_KEY}&language=tr-TR&append_to_response=videos"
                        try:
                            f_res = requests.get(full_movie_url, timeout=5)
                            movie_data = f_res.json() if f_res.status_code == 200 else m_credit
                        except:
                            movie_data = m_credit
                            
                        render_movie_card(movie_data, f"actor_credit_{idx}_{m_id}")
                else:
                    st.warning("Bu sanatçının akış kataloğu TMDB VOD kütüphanesinde boş görünüyor.")
        except Exception as e:
            st.error(f"Kanal verileri çekilirken hata: {str(e)}")

# -------------------------------------------------------------
# SEKME 2: MATRIX GRID SCANNER 
# -------------------------------------------------------------
with tab2:
    st.title("🔮 Grid Scanner Dev-Mode")
    render_status_dashboard(st.session_state.s2_cap, st.session_state.s2_status)
    manual_url = st.text_input("IPTV Adresi:", value="http://example.com:8080/get.php?username=demo&password=demo", key="s2_input")
    s2_depth = st.slider("Matris Derinliği (+/-)", 5, 50, 15, key="s2_slider")
    
    if st.button("Yan Siber Akışları Doğrula", key="s2_btn") and manual_url:
        st.session_state.s2_status = "Aktif (Tarıyor)"
        try:
            parsed = urlparse(manual_url)
            scheme, netloc = parsed.scheme, parsed.netloc
            domain = netloc.split(":")[0]
            port = ":" + netloc.split(":")[1] if ":" in netloc else ""
            queries = parse_qs(parsed.query)
            u = queries.get('username', ['demo'])[0]
            p = queries.get('password', ['demo'])[0]
            
            variants = []
            nums = re.findall(r'\d+', domain)
            if nums:
                base = int(nums[0])
                for v in range(max(0, base - s2_depth), base + s2_depth + 1):
                    new_host = domain.replace(str(base), str(v), 1)
                    variants.append(f"{scheme}://{new_host}{port}/get.php?username={u}&password={p}&type=m3u_plus")
            
            p_bar2 = st.progress(0)
            nodes = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=15) as exec2:
                tasks2 = {exec2.submit(parse_and_validate_xtream, vr): vr for vr in list(set(variants))}
                for idx, t in enumerate(concurrent.futures.as_completed(tasks2)):
                    r = t.result()
                    if r:
                        nodes.append(r["url"])
                        st.success(f"🟢 YAKALANDI: {r['url']}")
                    p_bar2.progress((idx + 1) / len(tasks2))
            st.session_state.s2_status = "Tamamlandı"
        except: st.session_state.s2_status = "Pasif"

# -------------------------------------------------------------
# SEKME 3: XTREAM CONTROLLER (DOSYA YÜKLEME & TXT ÇIKTI)
# -------------------------------------------------------------
with tab3:
    st.title("📺 Xtream Account Stream Validation")
    render_status_dashboard(st.session_state.s3_cap, st.session_state.s3_status)
    
    # Çoklu Giriş Katmanı: Dosya veya Metin Alanı
    col_up1, col_up2 = st.columns(2)
    with col_up1:
        uploaded_file = st.file_uploader("📂 Liste Yükle (.txt)", type=["txt"], key="s3_file_uploader")
    with col_up2:
        input_list = st.text_area("Metin olarak M3U / Xtream Linklerini Yapıştırın:", height=68, key="s3_area")
    
    # İki veri girişini birleştirme mantığı
    final_links = []
    if uploaded_file is not None:
        file_content = uploaded_file.read().decode("utf-8")
        final_links.extend([l.strip() for l in file_content.split("\n") if l.strip().startswith("http")])
    if input_list.strip():
        final_links.extend([l.strip() for l in input_list.split("\n") if l.strip().startswith("http")])
        
    final_links = list(set(final_links)) # Duplicate önleme

    if st.button("Hesap Detaylarını Çıkar ve Ayıkla", key="s3_btn") and final_links:
        st.session_state.s3_status = "Aktif (Tarıyor)"
        st.session_state.active_xtream_results = [] # Reset hafıza
        
        st.session_state.s3_cap = f"{len(final_links)} Link Analizde"
        p_bar3 = st.progress(0)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as exec3:
            tasks3 = {exec3.submit(parse_and_validate_xtream, lk): lk for lk in final_links}
            for idx, t in enumerate(concurrent.futures.as_completed(tasks3)):
                res = t.result()
                if res:
                    st.session_state.active_xtream_results.append(res)
                    if res["type"] == "Xtream_API":
                        st.markdown(f"""
                        <div class='neon-card'>
                            <h4>🟢 ÇALIŞIYOR (HESAP DETAYI YAKALANDI)</h4>
                            <b>🌍 Sunucu:</b> {res['server']} | <b>🔑 User:</b> {res['username']} | <b>🔒 Pass:</b> {res['password']}<br>
                            <b>📅 Bitiş:</b> {res['exp_date']} | <b>⚡ Durum:</b> {res['status']} | <b>👥 Bağlantı:</b> {res['max_connections']} Kişilik (Aktif: {res['active_cons']})
                        </div>
                        """, unsafe_allow_html=True)
                        c1, c2 = st.columns(2)
                        with c1: st.text_area("Xtream Kopyala", f"URL: {res['server']}\nUser: {res['username']}\nPass: {res['password']}", height=85, key=f"xc_{idx}")
                        with c2: st.text_area("M3U Link Kopyala", res["url"], height=85, key=f"m3u_{idx}")
                    else:
                        st.markdown(f"<div class='neon-card' style='border-left-color: #33b5e5;'>🔵 AKTİF M3U AKIŞI: {res['url']}</div>", unsafe_allow_html=True)
                        st.text_area("M3U URL Kopyala", res["url"], height=50, key=f"st_link_{idx}")
                p_bar3.progress((idx + 1) / len(final_links))
        st.session_state.s3_status = "Tamamlandı"

    # AKTİFLERİ .TXT OLARAK DIŞARI AKTARMA BUTONU
    if st.session_state.active_xtream_results:
        st.write("---")
        txt_lines = []
        for r in st.session_state.active_xtream_results:
            if r["type"] == "Xtream_API":
                txt_lines.append(f"Sunucu: {r['server']} | User: {r['username']} | Pass: {r['password']} | Bitiş: {r['exp_date']} | M3U: {r['url']}")
            else:
                txt_lines.append(f"M3U Akis: {r['url']}")
        
        txt_data = "\n".join(txt_lines)
        
        st.download_button(
            label="📥 AKTİF LİNKLERİ .TXT OLARAK İNDİR",
            data=txt_data,
            file_name=f"aktif_iptv_listesi_{datetime.now().strftime('%d_%m_%Y')}.txt",
            mime="text/plain"
        )
