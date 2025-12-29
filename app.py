import streamlit as st
import pandas as pd
import random
import re
import base64
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- 設定 ---
# 【重要】ご自身のスプレッドシートIDに書き換えてください
SPREADSHEET_ID = "あなたのスプレッドシートIDをここに貼り付け"
RANGE_NAME = "シート1!A:Z" # メンバーが増えることを見越して範囲を広げています

# --- 音を鳴らすための機能 ---
def play_sound(file_path):
    try:
        with open(file_path, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            md = f'<audio autoplay="true"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
            st.markdown(md, unsafe_allow_html=True)
    except:
        pass

# --- Google Sheets API 接続 ---
def get_sheets_service():
    info = st.secrets["gcp_service_account"]
    creds = service_account.Credentials.from_service_account_info(info)
    service = build("sheets", "v4", credentials=creds)
    return service.spreadsheets()

def load_data_from_sheets(master_data):
    try:
        sheets = get_sheets_service()
        result = sheets.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
        values = result.get("values", [])
        
        if not values or len(values) < 1:
            # 完全に空の場合は初期状態（家族4人）を作成
            initial_players = ["英明", "浄子", "悠奈", "千紘"]
            df = pd.DataFrame(columns=["kami"] + initial_players)
            df["kami"] = master_data["kami"]
            for p in initial_players:
                df[p] = "0"
            return df
            
        df = pd.DataFrame(values[1:], columns=values[0])
        return df
    except Exception as e:
        st.error(f"読み込みエラー: {e}")
        return pd.DataFrame()

def save_to_sheets(df):
    try:
        sheets = get_sheets_service()
        # NaN（空欄）を "0" に置き換えてから保存
        save_df = df.fillna("0")
        body = {"values": [save_df.columns.tolist()] + save_df.values.tolist()}
        sheets.values().update(
            spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME,
            valueInputOption="USER_ENTERED", body=body
        ).execute()
    except Exception as e:
        st.error(f"保存エラー: {e}")

def format_ruby(text):
    if not isinstance(text, str): return text
    return re.sub(r'([一-龠]+)\(([^)]+)\)', r'<ruby>\1<rt>\2</rt></ruby>', text)

# --- メイン処理 ---
master_data = pd.read_csv("hi.csv", encoding='utf-8_sig')

if 'app_stage' not in st.session_state:
    st.session_state.app_stage = 'start'

# A. スタート画面
if st.session_state.app_stage == 'start':
    st.title("百人一首マスターへの道")
    
    progress_df = load_data_from_sheets(master_data)
    # スプレッドシートの1行目からプレイヤー名（kami以外）を取得
    current_players = [col for col in progress_df.columns if col != 'kami']
    
    st.write("### だれが あそぶ？ 名前をえらんでね")
    # プレイヤーが多い場合は複数行に分けて表示
    cols = st.columns(3)
    for i, p in enumerate(current_players):
        if cols[i % 3].button(p, key=f"p_{p}", use_container_width=True):
            st.session_state.current_player = p
            st.session_state.app_stage = 'quiz'
            st.rerun()
            
    st.write("---")
    # 新規メンバー追加エリア
    with st.expander("➕ 新しいメンバーを追加する"):
        new_name = st.text_input("お名前を入力（例：おじいちゃん）")
        if st.button("登録してスタート"):
            if new_name and new_name not in current_players:
                # 新しい列を全行 "0" で追加
                progress_df[new_name] = "0"
                save_to_sheets(progress_df)
                st.session_state.current_player = new_name
                st.session_state.app_stage = 'quiz'
                st.







