import streamlit as st
import random
import pandas as pd

st.title("こども百人一首クイズ")

# CSVデータの読み込み
@st.cache_data
def load_data():
    # encoding='shift-jis' はExcelで作ったCSVを読み込むためのおまじないです
    df = pd.read_csv("hi.csv", encoding='utf-8') 
    return df.to_dict(orient='records')

try:
    data = load_data()

    if 'quiz' not in st.session_state:
        target = random.choice(data)
        # データ数に合わせて選択肢の数を調整（最大4つ）
        num_options = min(len(data) - 1, 3)
        wrong_options = random.sample([d['shimo'] for d in data if d != target], num_options)
        
        options = [target['shimo']] + wrong_options
        random.shuffle(options)
        st.session_state.quiz = {'target': target, 'options': options, 'answered': False}

    q = st.session_state.quiz

    st.subheader("【上の句】")
    st.write(f"### {q['target']['kami']}")
    st.caption(f"作者：{q['target']['author']}")

    st.divider()
    st.write("どの【下の句】が合うかな？")

    # 選択肢ボタンを横並びにする
    cols = st.columns(2)
    for i, opt in enumerate(q['options']):
        with cols[i % 2]:
            if st.button(opt, key=f"btn_{i}", use_container_width=True):
                if opt == q['target']['shimo']:
                    st.success("✨ せいかい！ ✨")
                    st.balloons()
                else:
                    st.error(f"ざんねん！ 正解は...\n\n「{q['target']['shimo']}」でした。")
                st.session_state.quiz['answered'] = True

    if st.button("つぎのもんだいへ ➔"):
        if 'quiz' in st.session_state:
            del st.session_state.quiz
        st.rerun()

except FileNotFoundError:
    st.error("「hi.csv」が見つかりません。app.pyと同じ場所に保存してください。")
