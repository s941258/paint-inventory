import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="雲端模型漆庫存", layout="wide")

# 建立 Google Sheets 連線
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    return conn.read(ttl="0s")

def save_data(df_new):
    conn.update(data=df_new)
    st.cache_data.clear()

df = load_data()
# 已加入 摩多MODO
BRS = ["九五二漆", "摩多MODO", "Airbeast", "Stedi", "Mr.Hobby", "AV", "Citadel", "AK", "Tamiya", "E7", "Gaia", "其他"]

# --- 側邊欄：新增與功能 ---
with st.sidebar:
    st.header("➕ 新增油漆")
    with st.form("add_form", clear_on_submit=True):
        nb = st.selectbox("品牌", BRS)
        ni = st.text_input("色號")
        nn = st.text_input("名稱")
        nt = st.text_input("標籤 (空格隔開)", placeholder="例如：噴塗 螢光 金屬")
        nq = st.number_input("數量", 0, 999, 1)
        nu = st.text_input("圖片網址 (方案A)")
        if st.form_submit_button("同步至雲端"):
            new_row = pd.DataFrame([[nb, ni, nn, nq, nu, nt]], columns=df.columns)
            df = pd.concat([df, new_row], ignore_index=True)
            save_data(df)
            st.success("同步成功！")
            st.rerun()

# --- 主畫面：標題與搜尋模式 ---
st.title("☁️ 模型漆雲端管理系統")

# 第一列：關鍵字搜尋與模式切換
c1, c2 = st.columns([3, 1])
with c1:
    search = st.text_input("🔍 關鍵字搜尋", placeholder="搜尋色號或名稱...", label_visibility="collapsed")
with c2:
    view_mode = st.radio("顯示模式", ["列表", "網格"], horizontal=True, label_visibility="collapsed")

# 第二列：進階篩選 (品牌與標籤)
f1, f2 = st.columns(2)
with f1:
    selected_brands = st.multiselect("過濾品牌", options=BRS, placeholder="選擇一個或多個品牌")

with f2:
    # 自動從現有資料中提取所有標籤 (去重並排序)
    all_tags = set()
    df['標籤'].fillna('').str.split().apply(all_tags.update)
    available_tags = sorted([t for t in list(all_tags) if t])
    selected_tags = st.multiselect("過濾功能/標籤", options=available_tags, placeholder="例如：噴塗、筆塗")

# --- 過濾資料邏輯 ---
v_df = df.copy()

if search:
    v_df = v_df[v_df.apply(lambda r: r.astype(str).str.contains(search, case=False).any(), axis=1)]

if selected_brands:
    v_df = v_df[v_df['品牌'].isin(selected_brands)]

if selected_tags:
    v_df = v_df[v_df['標籤'].fillna('').apply(lambda t: any(tag in t.split() for tag in selected_tags))]

st.divider()

# --- 顯示邏輯 ---
if not v_df.empty:
    if view_mode == "列表":
        for idx, r in v_df.iterrows():
            col_img, col_info, col_btn = st.columns([1, 4, 2])
            with col_img:
                if r['圖片路徑'] and str(r['圖片路徑']).startswith('http'):
                    st.image(r['圖片路徑'], use_container_width=True)
                else: st.write("🎨")
            with col_info:
                tag_display = f" <small style='color:blue;'>[{r['標籤']}]</small>" if r['標籤'] else ""
                st.markdown(f"**[{r['品牌']}]** {r['色號']}\n\n{r['名稱']}{tag_display}", unsafe_allow_html=True)
                st.write(f"庫存: **{int(r['庫存數量'])}**")
            with col_btn:
                b1, b2, b3 = st.columns(3)
                if b1.button("➕", key=f"p_l_{idx}"):
                    df.at[idx, '庫存數量'] += 1; save_data(df); st.rerun()
                if b2.button("➖", key=f"m_l_{idx}") and df.at[idx, '庫存數量'] > 0:
                    df.at[idx, '庫存數量'] -= 1; save_data(df); st.rerun()
                if b3.button("🗑️", key=f"d_l_{idx}"):
                    df = df.drop(idx); save_data(df); st.rerun()
            st.divider()
    else: # 網格模式
        n_cols = 3
        for i in range(0, len(v_df), n_cols):
            cols = st.columns(n_cols)
            batch = v_df.iloc[i : i + n_cols]
            for j, (idx, r) in enumerate(batch.iterrows()):
                with cols[j]:
                    if r['圖片路徑'] and str(r['圖片路徑']).startswith('http'):
                        st.image(r['圖片路徑'], use_container_width=True)
                    else: st.markdown("### 🎨")
                    st.markdown(f"**{r['色號']}** ({r['品牌']})")
                    st.caption(f"{r['名稱']}")
                    st.write(f"庫存: **{int(r['庫存數量'])}**")
                    b1, b2, b3 = st.columns(3)
                    if b1.button("➕", key=f"p_g_{idx}"):
                        df.at[idx, '庫存數量'] += 1; save_data(df); st.rerun()
                    if b2.button("➖", key=f"m_g_{idx}") and df.at[idx, '庫存數量'] > 0:
                        df.at[idx, '庫存數量'] -= 1; save_data(df); st.rerun()
                    if b3.button("🗑️", key=f"d_g_{idx}"):
                        df = df.drop(idx); save_data(df); st.rerun()
                    st.write("---")
else:
    st.info("找不到符合條件的油漆。")
