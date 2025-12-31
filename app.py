import streamlit as st
import pandas as pd
import random
import re
import base64
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- 設定 ---
# 【重要】ご自身のスプレッドシートIDに書き換えてください
SPREADSHEET_ID = "1npMBT--ZtreVNwwZh2Qo2zb7VJNu6wctxm5oELtPstA"
RANGE_NAME = "シート1!A:Z"

# --- 1. 音を鳴らすための機能 ---
def play_sound(file_path):
    try:
        with open(file_path, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            md = f'<audio autoplay="true"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
            st.markdown(md, unsafe_allow_html=True)
    except:
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
        
        if not values or len(values) < 1:
            # 初期プレイヤー設定
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

# --- 3. メイン処理 ---
# CSV読み込み（kami, shimo, author, yaku の列がある前提）
master_data = pd.read_csv("hi.csv", encoding='utf-8_sig')

if 'app_stage' not in st.session_state:
    st.session_state.app_stage = 'start'

# A. スタート画面
if st.session_state.app_stage == 'start':
    st.title("百人一首 3点先取マスターへの道")
    progress_df = load_data_from_sheets(master_data)
    current_players = [col for col in progress_df.columns if col != 'kami']
    
    st.write("### だれが あそぶ？")
    cols = st.columns(3)
    for i, p in enumerate(current_players):
        if cols[i % 3].button(p, key=f"p_{p}", use_container_width=True):
            st.session_state.current_player = p
            st.session_state.app_stage = 'quiz'
            st.rerun()
            
    st.write("---")
    with st.expander("➕ 新しいメンバーを追加する"):
        new_name = st.text_input("お名前を入力")
        if st.button("登録してスタート"):
            if new_name and new_name not in current_players:
                progress_df[new_name] = "0"
                save_to_sheets(progress_df)
                st.session_state.current_player = new_name
                st.session_state.app_stage = 'quiz'
                st.rerun()

# B. クイズ画面
elif st.session_state.app_stage == 'quiz':
    player = st.session_state.current_player
    progress_df = load_data_from_sheets(master_data)

    # 点数を数値に変換してマスター状況を確認
    scores = pd.to_numeric(progress_df[player], errors='coerce').fillna(0).astype(int)
    mastered_indices = scores[scores >= 3].index.tolist()
    mastered_count = len(mastered_indices)
    total_count = len(master_data)

    st.title(f"{player}さんの クイズ")
    st.progress(int(mastered_count / total_count * 100))
    st.write(f"マスターした数: {mastered_count} / {total_count}")

    # 出題対象（3点未満の歌）
    unmastered_indices = scores[scores < 3].index.tolist()

    if not unmastered_indices:
        st.balloons()
        st.success("全ての歌をマスターしました！おめでとう！")
        if st.button("スタートにもどる"):
            st.session_state.app_stage = 'start'
            st.rerun()
    else:
        if 'quiz' not in st.session_state:
            target_idx = random.choice(unmastered_indices)
            target = master_data.iloc[target_idx].to_dict()
            current_score = int(scores[target_idx])
            
            wrong = random.sample([d for d in master_data['shimo'] if d != target['shimo']], 3)
            options = [target['shimo']] + wrong
            random.shuffle(options)
            st.session_state.quiz = {
                'target': target, 'options': options, 'answered': False, 
                'idx': target_idx, 'score_before': current_score
            }

        q = st.session_state.quiz
        author_name = q['target'].get('author', '作者不明')
        stars = "★" * q['score_before'] + "☆" * (3 - q['score_before'])
        
        st.write(f"マスター度: {stars} ｜ **作者: {author_name}**")
        st.markdown(f"## {format_ruby(q['target']['kami'])}", unsafe_allow_html=True)
        st.write("---")
        
        for i, opt in enumerate(q['options']):
            st.markdown(format_ruby(opt), unsafe_allow_html=True)
            if st.button("これ！", key=f"btn_{i}", use_container_width=True):
                if not q['answered']:
                    new_score = q['score_before']
                    if opt == q['target']['shimo']:
                        new_score = min(3, q['score_before'] + 1)
                        st.success(f"✨ 正解！ ({q['score_before']}点 → {new_score}点) ✨")
                        play_sound("correct.mp3")
                        
                        # 正解時に作者と訳を表示
                        info_box = f"👤 **作者**：{author_name}\n\n"
                        if 'yaku' in q['target'] and pd.notna(q['target']['yaku']):
                            info_box += f"💡 **現代語訳**：\n\n{q['target']['yaku']}"
                        st.info(info_box)

                        if new_score == 3:
                            st.balloons()
                            st.write(f"🎊 【{author_name}】の歌をマスターしました！ 🎊")
                    else:
                        new_score = max(0, q['score_before'] - 1)
                        st.error(f"ざんねん！ 正解は... \n\n {q['target']['shimo']} \n\n (-1点：{q['score_before']}点 → {new_score}点)")
                        play_sound("wrong.mp3")
                        
                        # 不正解時も作者と訳を表示
                        st.write(f"👤 **作者**: {author_name}")
                        if 'yaku' in q['target'] and pd.notna(q['target']['yaku']):
                            st.write(f"💡 **現代語訳**: {q['target']['yaku']}")
                    
                    progress_df.at[q['idx'], player] = str(new_score)
                    save_to_sheets(progress_df)
                    st.session_state.quiz['answered'] = True

        st.write("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("つぎのもんだいへ ➔"):
                if 'quiz' in st.session_state: del st.session_state.quiz
                st.rerun()
