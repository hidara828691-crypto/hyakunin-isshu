import streamlit as st
import pandas as pd
import random
import re
import base64

# 音声を再生するための関数
def play_sound(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
            <audio autoplay="true">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        st.markdown(md, unsafe_allow_html=True)

# ルビを表示するための関数
def format_ruby(text):
    if not isinstance(text, str): return text
    return re.sub(r'([一-龠]+)\(([^)]+)\)', r'<ruby>\1<rt>\2</rt></ruby>', text)

st.title("百人一首クイズ")

@st.cache_data
def load_data():
    return pd.read_csv("hi.csv", encoding='utf-8_sig').to_dict(orient='records')

try:
    data = load_data()
    if 'quiz' not in st.session_state:
        target = random.choice(data)
        wrong = random.sample([d['shimo'] for d in data if d != target], 3)
        options = [target['shimo']] + wrong
        random.shuffle(options)
        st.session_state.quiz = {'target': target, 'options': options, 'answered': False}

    q = st.session_state.quiz

    st.subheader("【上の句】")
    st.markdown(f"## {format_ruby(q['target']['kami'])}", unsafe_allow_html=True)
    st.caption(f"作者：{q['target']['author']}")

    st.divider()

    for i, opt in enumerate(q['options']):
        st.markdown(format_ruby(opt), unsafe_allow_html=True)
        if st.button("これ！", key=f"btn_{i}", use_container_width=True):
            if not q['answered']:
                if opt == q['target']['shimo']:
                    st.success("✨ せいかい！ ✨")
                    st.balloons()
                    play_sound("correct.mp3") # 正解音
                else:
                    st.error(f"ざんねん！ 正解は...\n\n「{q['target']['shimo']}」でした。")
                    play_sound("wrong.mp3")   # 不正解音
                st.session_state.quiz['answered'] = True

    if st.button("つぎのもんだいへ ➔"):
        del st.session_state.quiz
        st.rerun()

except Exception as e:
    st.error(f"エラー: {e}")



