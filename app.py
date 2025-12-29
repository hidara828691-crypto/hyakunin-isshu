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

# --- 1. 音を鳴らすための機能（これが抜けていた可能性があります） ---
def play_sound(file_path):
    try:
        with open(file_path, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            md = f'<audio autoplay="true"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
            st.markdown(md, unsafe_allow_html=True)
    except Exception as e:
        # 音声ファイルがない場合はエラーを出さずに無視する
        pass

# --- 2. Google Sheets API 接続 ---
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
        
        if not values or len(values) < 2:
            df = pd.DataFrame(columns=["kami"] + PLAYERS)
            df["kami"] = master_data["kami"]
            for p in PLAYERS:
                df[p] = "0"
            return df
            
        return pd.DataFrame(values[1:], columns=values[0])
    except Exception as e:
        st.error(f"スプレッドシートの読み込みエラー: {e}")
        return pd.DataFrame()

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

# --- 3. アプリのメイン処理 ---

# データの読み込み
master_data = pd.read_csv("hi.csv", encoding='utf-8_sig')

if 'app_stage' not in st.session_state:
    st.session_state.app_stage = 'start'

# A. スタート画面
if st.session_state.app_stage == 'start':
    st.title("百人一首マスターへの道")
    st.write("### だれが あそぶ？ 名前をえらんでね")
    cols = st.columns(len(PLAYERS))
    for i, p in enumerate(PLAYERS):
        if cols[i].button(p, use_container_width=True):
            st.session_state.current_player = p
            st.session_state.app_stage = 'quiz'
            st.rerun()

# B. クイズ画面
elif st.session_state.app_stage == 'quiz':
    player = st.session_state.current_player
    progress_df = load_data_from_sheets(master_data)

    learned_indices = progress_df[progress_df[player].astype(str) == "1"].index.tolist()
    learned_count = len(learned_indices)
    total_count = len(master_data)

    st.title(f"{player}さんの クイズ")
    st.progress(int(learned_count / total_count * 100))
    st.write(f"いままでにおぼえた数: {learned_count} / {total_count}")

    unlearned_indices = [i for i in range(total_count) if i not in learned_indices]

    if not unlearned_indices:
        st.balloons()
        st.success("コンプリート！")
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
        st.write("---")
        
        for i, opt in enumerate(q['options']):
            st.markdown(format_ruby(opt), unsafe_allow_html=True)
            if st.button("これ！", key=f"btn_{i}", use_container_width=True):
                if not q['answered']:
                    if opt == q['target']['shimo']:
                        st.success("✨ 正解！ ✨")
                        play_sound("correct.mp3")
                        progress_df.at[q['idx'], player] = "1"
                        save_to_sheets(progress_df)
                    else:
                        st.error(f"ざんねん！ 正解は... \n\n {q['target']['shimo']}")
                        play_sound("wrong.mp3")
                    st.session_state.quiz['answered'] = True

        st.write("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("つぎのもんだいへ ➔"):
                if 'quiz' in st.session_state: del st.session_state.quiz
                st.rerun()
        with col2:
            if st.button("きょうはおわる ☕"):
                st.session_state.app_stage = 'result'
                st.session_state.final_count = progress_df[player].astype(str).tolist().count("1")
                st.rerun()

# C. 終了画面
elif st.session_state.app_stage == 'result':
    st.title("お疲れ様でした！")
    player = st.session_state.current_player
    count = st.session_state.get('final_count', 0)
    st.write(f"### {player}さんは、これまでに")
    st.header(f"✨ {count}首 ✨")
    st.write("### おぼえることができました！")
    st.balloons()
    if st.button("タイトルにもどる"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# --- 画面を一番上に戻すための仕掛け ---
st.components.v1.html(
    """
    <script>
    window.parent.document.querySelector('section.main').scrollTo(0, 0);
    </script>
    """,
    height=0,
)






