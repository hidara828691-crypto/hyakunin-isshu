import streamlit as st
import pandas as pd
import random
import re

# ルビを表示するための関数
def format_ruby(text):
    # 漢字(ひらがな) を <ruby>タグに変換
    if not isinstance(text, str):
        return text
    formatted = re.sub(r'([一-龠]+)\(([^)]+)\)', r'<ruby>\1<rt>\2</rt></ruby>', text)
    return formatted

st.title("こども百人一首クイズ")

# CSVデータの読み込み
@st.cache_data
def load_data():
    # encoding='utf-8_sig' は文字化け防止用です
    df = pd.read_csv("hi.csv", encoding='utf-8_sig')
    return df.to_dict(orient='records')

# ここからがクイズのメイン処理
try:
    data = load_data()

    if 'quiz' not in st.session_state:
        target = random.choice(data)
        num_options = min(len(data) - 1, 3)
        wrong_options = random.sample([d['shimo'] for d in data if d != target], num_options)
        options = [target['shimo']] + wrong_options
        random.shuffle(options)
        st.session_state.quiz = {'target': target, 'options': options, 'answered': False}

    q = st.session_state.quiz

    st.subheader("【上の句】")
    # ルビ付きで上の句を表示
    st.markdown(f"## {format_ruby(q['target']['kami'])}", unsafe_allow_html=True)
    st.caption(f"作者：{q['target']['author']}")

    st.divider()
    st.write("どの【下の句】が合うかな？")

    # 選択肢ボタンの作成
    for i, opt in enumerate(q['options']):
        # ボタンの上にルビを表示
        st.markdown(format_ruby(opt), unsafe_allow_html=True)
        if st.button("これ！", key=f"btn_{i}", use_container_width=True):
            if opt == q['target']['shimo']:
                st.success("✨ せいかい！ ✨")
                st.balloons()
            else:
                st.error(f"ざんねん！ 正解は...\n\n「{q['target']['shimo']}」でした。")
            st.session_state.quiz['answered'] = True
        st.write("") # スペース空け

    if st.button("つぎのもんだいへ ➔"):
        if 'quiz' in st.session_state:
            del st.session_state.quiz
        st.rerun()

except FileNotFoundError:
    st.error("「hi.csv」が見つかりません。app.pyと同じ場所に保存してください。")
except Exception as e:
    st.error(f"エラーが発生しました: {e}")

