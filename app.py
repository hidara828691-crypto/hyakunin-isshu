import streamlit as st
import pandas as pd
import random
import re
import base64
import os

# --- 設定・便利関数 ---
PLAYERS = ["英明", "浄子", "悠奈", "千紘"]
PROGRESS_FILE = "progress.csv"

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

# --- データ管理 ---
@st.cache_data
def load_master_data():
    return pd.read_csv("hi.csv", encoding='utf-8_sig')

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        return pd.read_csv(PROGRESS_FILE)
    else:
        # 初回は全員未習得の表を作成
        df = load_master_data()
        progress = pd.DataFrame({'kami': df['kami']})
        for p in PLAYERS:
            progress[p] = 0 # 0:未習得, 1:習得済み
        return progress

def save_progress(df):
    df.to_csv(PROGRESS_FILE, index=False, encoding='utf-8_sig')

# --- メイン画面 ---
st.title("家族で百人一首マスター")

# 1. プレイヤー選択
player = st.sidebar.selectbox("だれが あそぶ？", PLAYERS)
progress_df = load_progress()

# 習得状況の表示
learned_count = progress_df[player].sum()
total_count = len(progress_df)
st.sidebar.write(f"### {player}さんの成績")
st.sidebar.progress(int(learned_count / total_count * 100))
st.sidebar.write(f"{total_count}首中 {learned_count}首 おぼえた！")

# 2. 出題データの準備
master_data = load_master_data()
# まだ覚えていない（値が0）歌のインデックスを取得
unlearned_indices = progress_df[progress_df[player] == 0].index.tolist()

if not unlearned_indices:
    st.balloons()
    st.success(f"おめでとうございます！{player}さんはすべての歌をマスターしました！")
    if st.button("記録をリセットしてもう一度遊ぶ"):
        progress_df[player] = 0
        save_progress(progress_df)
        st.rerun()
else:
    if 'quiz' not in st.session_state or st.session_state.get('current_player') != player:
        # 未習得の中からランダムに1つ選ぶ
        target_idx = random.choice(unlearned_indices)
        target = master_data.iloc[target_idx].to_dict()
        
        # 選択肢（全データからランダムに）
        wrong = random.sample([d for d in master_data['shimo'] if d != target['shimo']], 3)
        options = [target['shimo']] + wrong
        random.shuffle(options)
        
        st.session_state.quiz = {'target': target, 'options': options, 'answered': False, 'idx': target_idx}
        st.session_state.current_player = player

    q = st.session_state.quiz

    st.subheader(f"【{player}さんへの問題】")
    st.markdown(f"## {format_ruby(q['target']['kami'])}", unsafe_allow_html=True)
    
    for i, opt in enumerate(q['options']):
        st.markdown(format_ruby(opt), unsafe_allow_html=True)
        if st.button("これ！", key=f"btn_{i}", use_container_width=True):
            if not q['answered']:
                if opt == q['target']['shimo']:
                    st.success("✨ 正解！おぼえたね！ ✨")
                    play_sound("correct.mp3")
                    # 記録を更新
                    progress_df.at[q['idx'], player] = 1
                    save_progress(progress_df)
                else:
                    st.error(f"ざんねん！ 正解は... \n\n {q['target']['shimo']}")
                    play_sound("wrong.mp3")
                st.session_state.quiz['answered'] = True

    if st.button("つぎのもんだいへ ➔"):
        if 'quiz' in st.session_state: del st.session_state.quiz
        st.rerun()



