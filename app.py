import streamlit as st
import json
import random
import re

# --- データ読み込みとキャッシュ ---
@st.cache_data
def load_data(filepath="hyakunin_isshu.json"):
    """
    百人一首のJSONデータを読み込み、Streamlitのキャッシュに保存します。
    これにより、アプリの操作ごとに関数が再実行されるのを防ぎ、パフォーマンスを向上させます。
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"エラー: {filepath} が見つかりません。同じディレクトリに配置してください。")
        return None

# --- クイズの状態を初期化する関数 ---
def initialize_quiz(mode):
    """
    セッション状態を初期化またはリセットします。
    問題リストの生成、インデックスとスコアのリセットなどを行います。
    """
    st.session_state.mode = mode
    st.session_state.all_poems = load_data()
    
    if st.session_state.all_poems is None:
        return

    # 問題IDのリストを作成
    ids = [poem["id"] for poem in st.session_state.all_poems]
    
    # モードに応じてリストを並び替え
    if mode == "ランダム":
        random.shuffle(ids)
    else: # ID順
        ids.sort()
        
    st.session_state.question_list = ids
    
    # その他の状態をリセット
    st.session_state.current_question_index = 0
    st.session_state.score = 0
    st.session_state.is_answered = False
    # 現在の問題の選択肢と回答をクリア
    if "options" in st.session_state:
        del st.session_state.options
    if "user_last_answer" in st.session_state:
        del st.session_state.user_last_answer


# --- メインのアプリケーション処理 ---

# ページのタイトルとアイコンを設定
st.set_page_config(
    page_title="百人一首クイズ",
    page_icon="🌸"
)

st.title("百人一首クイズ 🌸")

# --- スマホ表示用のカスタムCSS ---
st.markdown("""
<style>
/* ラジオボタンの選択肢のスタイル調整 */
div[role="radiogroup"] > label {
    font-size: 1.1rem !important; /* フォントサイズを大きくする */
    line-height: 1.8 !important;   /* 行間を広げる */
    margin-bottom: 10px !important; /* 各選択肢の下に余白を追加 */
}
</style>
""", unsafe_allow_html=True)


# データ読み込み
all_poems = load_data()

if all_poems:
    # --- サイドバーでのモード選択 ---
    mode = st.sidebar.radio(
        "出題順を選択してください",
        ("ID順", "ランダム"),
        key="mode_selector"
    )

    # モードが変更された場合、または初回起動時にクイズを初期化
    if "mode" not in st.session_state or st.session_state.mode != mode:
        initialize_quiz(mode)

    # --- 問題の準備と表示 ---
    q_index = st.session_state.current_question_index
    
    # まだ問題が残っている場合
    if q_index < len(st.session_state.question_list):
        q_id = st.session_state.question_list[q_index]
        # IDを基に現在の問題の歌データを取得
        current_poem = next((p for p in all_poems if p["id"] == q_id), None)

        # 選択肢の生成（各問題の初回表示時のみ）
        if "options" not in st.session_state:
            correct_lower = current_poem["lower"]
            
            # 正解以外のすべての下の句をリストアップ
            all_lowers = [p["lower"] for p in all_poems if p["id"] != q_id]
            
            # 不正解の選択肢を3つランダムに選ぶ
            wrong_options = random.sample(all_lowers, 3)
            
            # 正解と不正解を結合してシャッフル
            options = wrong_options + [correct_lower]
            random.shuffle(options)
            
            # セッション状態で選択肢と正解を保持
            st.session_state.options = options
            st.session_state.correct_answer = correct_lower

        # --- 画面表示 ---
        st.header(f"第 {q_index + 1} 問")
        st.subheader(f"上の句: 「{current_poem['upper']}」")

        # 回答用のラジオボタン
        user_answer = st.radio(
            "下の句を選んでください",
            st.session_state.options,
            key=f"q_{q_id}",
            disabled=st.session_state.is_answered # 回答後は無効化
        )

        # --- ボタンと回答処理 ---
        # 回答済みの状態の時の処理
        if st.session_state.is_answered:
            # 正誤判定と結果表示
            if st.session_state.user_last_answer == st.session_state.correct_answer:
                st.success("正解！ 🎉")
            else:
                st.error(f"不正解... 正解は「{st.session_state.correct_answer}」でした。")
            
            # 歌の全体像と解説の表示
            with st.container(border=True):
                # フォントサイズを大きくするためのスタイルを定義
                style = """
                <style>
                .large-font {
                    font-size: 1.2rem; /* お好みのサイズに調整 */
                }
                </style>
                """
                st.markdown(style, unsafe_allow_html=True)
                
                st.markdown(f'<div class="large-font">{current_poem["upper"]}　{current_poem["lower"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="large-font"><span style="font-size: 1rem;">（{current_poem["reading_upper"]}　{current_poem["reading_lower"]}）</span></div>', unsafe_allow_html=True)
                st.markdown("---")
                
                # 既存の解説文の整形と表示
                desc_text = current_poem['description']
                #余計な空白文字を削除
                desc_text = desc_text.strip()

                desc_text = desc_text.replace("【出典】", "\n\n【出典】")  
                desc_text = desc_text.replace("【背景・情景】", "\n\n【背景・情景】")
                desc_text = desc_text.replace("【文学的ポイント】", "\n\n【文学的ポイント】")

                # st.markdown(f"【詠み手】 {current_poem['author']}")
                # st.markdown(desc_text)

                
                st.markdown(f'<div class="large-font">【詠み手】: {current_poem["author"]}\n\n</div><br>', unsafe_allow_html=True)
                st.markdown(f'<div class="large-font">{desc_text}</div>', unsafe_allow_html=True)
                        








                # st.markdown(f"**{current_poem['upper']}　{current_poem['lower']}**")
                # st.caption(f"（{current_poem['reading_upper']}　{current_poem['reading_lower']}）")
                # st.markdown("---")
                
                # 解説文の整形
                # desc_text = current_poem['description']




                # 余計な空白文字を削除
                # desc_text = desc_text.strip()

                # desc_text = desc_text.replace("【出典】", "\n\n【出典】")  
                # desc_text = desc_text.replace("【背景・情景】", "\n\n【背景・情景】")
                # desc_text = desc_text.replace("【文学的ポイント】", "\n\n【文学的ポイント】")

                # st.markdown(f"【詠み手】 {current_poem['author']}")
                # st.markdown(desc_text)


            # 「次の問題へ」ボタン
            if st.button("次の問題へ", key="next_button"):
                st.session_state.current_question_index += 1
                st.session_state.is_answered = False
                # 次の問題のためにセッション情報をクリア
                del st.session_state.options
                del st.session_state.user_last_answer
                st.rerun()
        
        # 未回答の状態の時の処理
        else:
            # 「回答」ボタン
            if st.button("回答する", key="submit_button"):
                # ユーザーの回答を保存し、状態を「回答済み」に更新
                st.session_state.user_last_answer = user_answer
                st.session_state.is_answered = True
                
                # 正解ならスコアをここで加算
                if user_answer == st.session_state.correct_answer:
                    st.session_state.score += 1
                
                # 画面を再実行して結果を表示
                st.rerun()

    # --- 全問終了後の結果表示 ---
    else:
        st.header("クイズ終了！")
        st.balloons()
        st.subheader(f"あなたのスコア: {st.session_state.score} / {len(st.session_state.question_list)} 点")
        
        if st.button("もう一度挑戦する", key="retry_button"):
            # 同じモードで再度初期化
            initialize_quiz(st.session_state.mode)
            st.rerun()
