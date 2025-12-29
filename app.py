import streamlit as st
import pandas as pd
import random
import re
import base64
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- 設定 ---
PLAYERS = ["英明", "浄子", "悠奈", "千紘"]
SPREADSHEET_ID = "1npMBT--ZtreVNwwZh2Qo2zb7VJNu6wctxm5oELtPstA"
RANGE_NAME = "シート1!A:E"

# --- Google Sheets API 接続関数 ---
def get_sheets_service():
    info = st.secrets["gcp_service_account"]
    creds = service_account.Credentials.from_service_account_info(info)
    service = build("sheets", "v4", credentials=creds)
    return service.spreadsheets()

def load_data_from_sheets():
    sheets = get_sheets_service()
    result = sheets.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    values = result.get("values", [])
    if not values: return pd.DataFrame()
    return pd.DataFrame(values[1:], columns=values[0])

def save_to_sheets(df):
    sheets = get_sheets_service()
    body = {"values": [df.columns.tolist()] + df.values.tolist()}
    sheets.values().update(
        spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME,
        valueInputOption="USER_ENTERED", body=body
    ).execute()

def format_ruby(text):
    if not isinstance(text, str): return text
    return re.sub(r'([一-龠]+)\(([^)]+)\)', r'<ruby>\1<rt>\2</rt></ruby>', text)

# --- アプリの状態管理 ---
if 'app_stage' not in st.session_state:
    st.session_state.app_stage = 'start' # 'start', 'quiz', 'result'

# --- 1. スタート画面（名前選択） ---
if st.session_state.app_stage == 'start':
    st.title("百人一首マスターへの道")
    st.write("### だれが あそぶ？ 名前をえらんでね")
    
    cols = st.columns(len(PLAYERS))
    for i, p in enumerate(PLAYERS):
        if cols[i].button(p, use_container_width=True):
            st.session_state.current_player = p
            st.session_state.app_stage = 'quiz'
            st.rerun()

# --- 2. クイズ画面 ---
elif st.session_state.app_stage == 'quiz':
    player = st.session_state.current_player
    master_data = pd.read_csv("hi.csv", encoding='utf-8_sig')
    progress_df = load_data_from_sheets()

    # 進捗計算
    learned_indices = progress_df[progress_df[player].astype(str) == "1"].index.tolist()
    learned_count = len(learned_indices)
    total_count = len(master_data)

    st.title(f"{player}さんの クイズ")
    st.progress(int(learned_count / total_count * 100))
    st.write(f"いままでにおぼえた数: {learned_count} / {total_count}")

    unlearned_indices = [i for i in range(total_count) if i not in learned_indices]

    if not unlearned_indices:
        st.balloons()
        st.success("コンプリート！おめでとうございます！")
        if st.button("スタートにもどる"):
            st.session_state.app_stage = 'start'
            st.rerun()
    else:
        if 'quiz' not in st.session_state:
            target_idx = random.choice(unlearned_indices)
            target = master_data.iloc[target_idx].to_dict()
            wrong = random.sample([d for d in master_data['shimo'] if d != target['shimo']], 3)
            options = [target['shimo']] + wrong
            random.shuffle(options)
            st.session_state.quiz = {'target': target, 'options': options, 'answered': False, 'idx': target_idx}

        q = st.session_state.quiz
        st.markdown(f"## {format_ruby(q['target']['kami'])}", unsafe_allow_html=True)
        
        for i, opt in enumerate(q['options']):
            if st.button(format_ruby(opt), key=f"btn_{i}", use_container_width=True):
                if not q['answered']:
# --- クイズ画面の中の判定部分を以下のように修正 ---
                if opt == q['target']['shimo']:
                    st.success("✨ 正解！ ✨")
                    play_sound("correct.mp3")  # ←これを追加
                    progress_df.at[q['idx'], player] = "1"
                    save_to_sheets(progress_df)
                else:
                    st.error(f"ざんねん！ 正解は... \n\n {q['target']['shimo']}")
                    play_sound("wrong.mp3")     # ←これを追加

        st.write("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("つぎのもんだいへ ➔"):
                if 'quiz' in st.session_state: del st.session_state.quiz
                st.rerun()
        with col2:
            if st.button("きょうはおわる ☕"):
                st.session_state.app_stage = 'result'
                st.session_state.final_count = learned_count + (1 if q.get('answered') and opt == q['target']['shimo'] else 0)
                st.rerun()

# --- 3. 終了画面（結果表示） ---
elif st.session_state.app_stage == 'result':
    st.title("お疲れ様でした！")
    player = st.session_state.current_player
    count = st.session_state.get('final_count', 0)
    
    st.write(f"### {player}さんは、これまでに")
    st.header(f"✨ {count}首 ✨")
    st.write("### おぼえることができました！")
    
    st.balloons()
    
    if st.button("タイトルにもどる"):
        # データをリセットして最初に戻る
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()




