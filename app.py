# --- クイズ画面の表示部分を修正 ---
        q = st.session_state.quiz
        
        # 1. 習得度と作者を表示
        stars = "★" * q['score_before'] + "☆" * (3 - q['score_before'])
        author_name = q['target'].get('author', '作者不明')
        
        st.write(f"マスター度: {stars} ｜ **作者: {author_name}**") # ここに作者を表示
        
        st.markdown(f"## {format_ruby(q['target']['kami'])}", unsafe_allow_html=True)
        st.write("---")
        
        # 2. 判定ボタン部分の修正
        for i, opt in enumerate(q['options']):
            st.markdown(format_ruby(opt), unsafe_allow_html=True)
            if st.button("これ！", key=f"btn_{i}", use_container_width=True):
                if not q['answered']:
                    new_score = q['score_before']
                    if opt == q['target']['shimo']:
                        new_score = min(3, q['score_before'] + 1)
                        st.success(f"✨ 正解！ ({q['score_before']}点 → {new_score}点) ✨")
                        play_sound("correct.mp3")
                        
                        # 正解時に「作者」と「訳」をセットで表示
                        info_text = f"👤 **作者**：{author_name}\n\n"
                        if 'yaku' in q['target'] and pd.notna(q['target']['yaku']):
                            info_text += f"💡 **現代語訳**：{q['target']['yaku']}"
                        st.info(info_text)

                        if new_score == 3:
                            st.balloons()
                            st.write(f"🎊 【{author_name}】の歌をマスターしました！ 🎊")
                    else:
                        new_score = max(0, q['score_before'] - 1)
                        st.error(f"ざんねん！ 正解は... \n\n {q['target']['shimo']}")
                        play_sound("wrong.mp3")
                        
                        # 不正解時も作者と訳を表示
                        st.write(f"👤 **作者**: {author_name}")
                        if 'yaku' in q['target'] and pd.notna(q['target']['yaku']):
                            st.write(f"💡 **現代語訳**: {q['target']['yaku']}")
                    
                    progress_df.at[q['idx'], player] = str(new_score)
                    save_to_sheets(progress_df)
                    st.session_state.quiz['answered'] = True

