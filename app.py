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
        if st.form_submit_button("同步至雲端"):
            new_row = pd.DataFrame([[nb, ni, nn, nq, "", nt]], columns=df.columns)
            df = pd.concat([df, new_row], ignore_index=True)
            save_data(df)
            st.success("同步成功！")
            st.rerun()

# --- 主畫面：搜尋與清單 ---
st.title("☁️ 模型漆雲端管理系統")
search = st.text_input("🔍 搜尋 (品牌、名稱、標籤...)", placeholder="例如：螢光")

v_df = df[df.apply(lambda r: r.astype(str).str.contains(search, case=False).any(), axis=1)] if search else df

if not v_df.empty:
   for idx, r in v_df.iterrows():
        # 建立三欄：圖片、資訊、操作按鈕
        col_img, col_info, col_btn = st.columns([1, 4, 2])
        
        # 1. 顯示圖片
        with col_img:
            if r['圖片路徑'] and str(r['圖片路徑']).startswith('http'):
                st.image(r['圖片路徑'], use_container_width=True)
            else:
                st.write("🎨") # 若無圖片則顯示圖示
        
        # 2. 顯示文字資訊
        with col_info:
            tag_str = f" <small style='color:blue;'>[{r['標籤']}]</small>" if r['標籤'] else ""
            st.markdown(f"**[{r['品牌']}]** {r['色號']}\n\n{r['名稱']}{tag_str}", unsafe_allow_html=True)
            st.write(f"庫存: **{int(r['庫存數量'])}**")
        
        # 3. 顯示操作按鈕
        with col_btn:
            b1, b2, b3 = st.columns(3)
            if b1.button("➕", key=f"p{idx}"):
                df.at[idx, '庫存數量'] += 1
                save_data(df); st.rerun()
            if b2.button("➖", key=f"m{idx}") and df.at[idx, '庫存數量'] > 0:
                df.at[idx, '庫存數量'] -= 1
                save_data(df); st.rerun()
            if b3.button("🗑️", key=f"d{idx}"):
                df = df.drop(idx)
                save_data(df); st.rerun()
        st.divider()
