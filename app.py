import streamlit as st
import pandas as pd
import random
import re
import base64
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- 設定 ---
PLAYERS = ["英明", "浄子", "悠奈", "千紘"]
# 【重要】作成したスプレッドシートのIDをここに貼り付けてください
SPREADSHEET_ID = "ここにスプレッドシートのIDを貼り付け"
RANGE_NAME = "シート1!A:E"

# --- Google Sheets API 接続関数 ---
def get_sheets_service():
    # Secretsから認証情報を取得
    info = st.secrets["gcp_service_account"]
    creds = service_account.Credentials.from_service_account_info(info)
    service = build("sheets", "v4", credentials=creds)
    return service.spreadsheets()

# --- データの読み書き ---
def load_data_from_sheets():
    sheets = get_sheets_service()
    result = sheets.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    values = result.get("values", [])
    if not values:
        return pd.DataFrame()
    return pd.DataFrame(values[1:], columns=values[0])

def save_to_sheets(df):
    sheets = get_sheets_service()
    body = {"values": [df.columns.tolist()] + df.values.tolist()}
    sheets.values().update(
        spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME,
        valueInputOption="USER_ENTERED", body=body
    ).execute()

# --- 便利関数 ---
def play_sound(file_path):
    try:
        with open(file_path, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            md = f'<audio autoplay="true"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
            st.markdown(md, unsafe_allow_html=True)
    except:
        pass

def format_ruby(text):
    if not isinstance(text, str): return text
    return re.sub(r'([一-龠]+)\(([^)]+)\)', r'<ruby>\1<rt>\2</rt></ruby>', text)

# --- メイン画面 ---
st.title("家族で百人一首マスター")

# 1. データの読み込み
master_data = pd.read_csv("hi.csv", encoding='utf-8_sig')
progress_df = load_data_from_sheets()

# 2. プレイヤー選択
player = st.sidebar.selectbox("だれが あそぶ？", PLAYERS)

# 習得状況の計算
# スプレッドシートの値は文字列なので比較に注意
learned_indices = progress_df[progress_df[player].astype(str) == "1"].index.tolist()
learned_count = len(learned_indices)
total_count = len(master_data)

st.sidebar.write(f"### {player}さんの成績")
st.sidebar.progress(int(learned_count / total_count * 100))
st.sidebar.write(f"{total_count}首中 {learned_count}首 おぼえた！")

# 3. 出題ロジック
unlearned_indices = [i for i in range(total_count) if i not in learned_indices]

if not unlearned_indices:
    st.balloons()
    st.success(f"おめでとうございます！{player}さんはすべての歌をマスターしました！")
else:
    if 'quiz' not in st.session_state or st.session_state.get('current_player') != player:
        target_idx = random.choice(unlearned_indices)
        target = master_data.iloc[target_idx].to_dict()
        wrong = random.sample([d for d in master_data['shimo'] if d != target['shimo']], 3)
        options = [target['shimo']] + wrong
        random.shuffle(options)
        st.session_state.quiz = {'target': target, 'options': options, 'answered': False, 'idx': target_idx}
        st.session_state.current_player = player

    q = st.session_state.quiz
    st.subheader(f"【{player}さんへの問題】")
    st.markdown(f"## {format_ruby(q['target']['kami'])}", unsafe_allow_html=True)
    
    for i, opt in enumerate(q['options']):
        if st.button(format_ruby(opt), key=f"btn_{i}", use_container_width=True):
            if not q['answered']:
                if opt == q['target']['shimo']:
                    st.success("✨ 正解！おぼえたね！ ✨")
                    play_sound("correct.mp3")
                    # スプレッドシートの値を更新 (1を書き込む)
                    progress_df.at[q['idx'], player] = "1"
                    save_to_sheets(progress_df)
                else:
                    st.error(f"ざんねん！ 正解は... \n\n {q['target']['shimo']}")
                    play_sound("wrong.mp3")
                st.session_state.quiz['answered'] = True

    if st.button("つぎのもんだいへ ➔"):
        if 'quiz' in st.session_state: del st.session_state.quiz
        st.rerun()




