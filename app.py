import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="雲端模型漆庫存", layout="wide")

# 建立 Google Sheets 連線
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    # ttl=0 確保每次重新整理都抓取 Google Sheets 最新資料
    return conn.read(ttl="0s")

def save_data(df_new):
    conn.update(data=df_new)
    st.cache_data.clear()

df = load_data()
BRS = ["九五二漆", "Airbeast", "Stedi", "Mr.Hobby", "AV", "Citadel", "AK", "Tamiya", "E7", "Gaia", "其他"]

# --- 側邊欄：新增與功能 ---
with st.sidebar:
    st.header("➕ 新增油漆")
    with st.form("add_form", clear_on_submit=True):
        nb = st.selectbox("品牌", BRS)
        ni = st.text_input("色號")
        nn = st.text_input("名稱")
        nt = st.text_input("標籤 (空格隔開)")
        nq = st.number_input("數量", 0, 999, 1)
        nu = st.text_input("圖片網址 (方案A)", placeholder="https://i.imgur.com/...")
        if st.form_submit_button("同步至雲端"):
            # 確保寫入順序與 Sheets 欄位一致
            new_row = pd.DataFrame([[nb, ni, nn, nq, nu, nt]], columns=df.columns)
            df = pd.concat([df, new_row], ignore_index=True)
            save_data(df)
            st.success("同步成功！")
            st.rerun()

# --- 主畫面：搜尋與切換 ---
# --- 主畫面：搜尋與進階篩選 ---
st.title("☁️ 模型漆雲端管理系統")

# 1. 第一層：關鍵字搜尋與模式切換
c1, c2 = st.columns([3, 1])
with c1:
    search = st.text_input("🔍 關鍵字搜尋", placeholder="搜尋色號、名稱...", label_visibility="collapsed")
with c2:
    view_mode = st.radio("顯示模式", ["列表", "網格"], horizontal=True, label_visibility="collapsed")

# 2. 第二層：進階分類篩選 (橫向排版)
f1, f2 = st.columns(2)
with f1:
    # 品牌多選
    selected_brands = st.multiselect("過濾品牌", options=BRS, placeholder="選擇品牌...")
with f2:
    # 提取所有標籤並去重 (假設標籤是用空格隔開)
    all_tags = set()
    df['標籤'].fillna('').str.split().apply(all_tags.update)
    selected_tags = st.multiselect("過濾功能/標籤", options=sorted(list(all_tags)), placeholder="例如：噴塗、筆塗...")

# --- 過濾資料邏輯 ---
v_df = df.copy()

# A. 關鍵字過濾
if search:
    v_df = v_df[v_df.apply(lambda r: r.astype(str).str.contains(search, case=False).any(), axis=1)]

# B. 品牌過濾 (如果有選的話)
if selected_brands:
    v_df = v_df[v_df['品牌'].isin(selected_brands)]

# C. 標籤過濾 (如果有選的話)
if selected_tags:
    # 只要漆料包含選中標籤的其中一個就顯示
    v_df = v_df[v_df['標籤'].fillna('').apply(lambda t: any(tag in t.split() for tag in selected_tags))]

st.divider()
# --- 接續原本的 if not v_df.empty: 顯示邏輯 ---

if not v_df.empty:
    if view_mode == "列表":
        for idx, r in v_df.iterrows():
            col_img, col_info, col_btn = st.columns([1, 4, 2])
            
            # 1. 列表圖片
            with col_img:
                if r['圖片路徑'] and str(r['圖片路徑']).startswith('http'):
                    st.image(r['圖片路徑'], use_container_width=True)
                else:
                    st.write("🎨")
            
            # 2. 列表資訊
            with col_info:
                tag_str = f" <small style='color:blue;'>[{r['標籤']}]</small>" if r['標籤'] else ""
                st.markdown(f"**[{r['品牌']}]** {r['色號']}\n\n{r['名稱']}{tag_str}", unsafe_allow_html=True)
                st.write(f"庫存: **{int(r['庫存數量'])}**")
            
            # 3. 列表操作
            with col_btn:
                b1, b2, b3 = st.columns(3)
                if b1.button("➕", key=f"p_l_{idx}"):
                    df.at[idx, '庫存數量'] += 1
                    save_data(df); st.rerun()
                if b2.button("➖", key=f"m_l_{idx}") and df.at[idx, '庫存數量'] > 0:
                    df.at[idx, '庫存數量'] -= 1
                    save_data(df); st.rerun()
                if b3.button("🗑️", key=f"d_l_{idx}"):
                    df = df.drop(idx)
                    save_data(df); st.rerun()
            st.divider()

    else:  # 網格模式
        # 每行顯示 3 個（電腦看剛好，手機看會自動堆疊）
        n_cols = 3
        for i in range(0, len(v_df), n_cols):
            cols = st.columns(n_cols)
            batch = v_df.iloc[i : i + n_cols]
            for j, (idx, r) in enumerate(batch.iterrows()):
                with cols[j]:
                    # 網格卡片設計
                    if r['圖片路徑'] and str(r['圖片路徑']).startswith('http'):
                        st.image(r['圖片路徑'], use_container_width=True)
                    else:
                        st.markdown("### 🎨")
                    
                    st.markdown(f"**{r['色號']}** ({r['品牌']})")
                    st.caption(f"{r['名稱']}")
                    st.write(f"庫存: **{int(r['庫存數量'])}**")
                    
                    # 網格縮小版按鈕
                    b1, b2, b3 = st.columns(3)
                    if b1.button("➕", key=f"p_g_{idx}"):
                        df.at[idx, '庫存數量'] += 1
                        save_data(df); st.rerun()
                    if b2.button("➖", key=f"m_g_{idx}") and df.at[idx, '庫存數量'] > 0:
                        df.at[idx, '庫存數量'] -= 1
                        save_data(df); st.rerun()
                    if b3.button("🗑️", key=f"d_g_{idx}"):
                        df = df.drop(idx)
                        save_data(df); st.rerun()
                    st.write("---")
else:
    st.info("找不到符合條件的油漆。")
