import streamlit as st
import sqlite3
from google import genai

# ==========================================
# 1. データベースとAIの準備
# ==========================================
conn = sqlite3.connect('my_language_app.db', check_same_thread=False)
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS vocabulary (
        word TEXT, meaning TEXT, memo TEXT
    )
''')
conn.commit()

# ★ここに、先ほど取得したあなたのAPIキーを貼り付けます！
# 例: client = genai.Client(api_key="AIzaSy...")
import os
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# ==========================================
# 2. アプリの画面（AIへの入力）
# ==========================================
st.title("🤖 AI自動生成・単語帳アプリ")

st.write("調べたい単語を入力すると、AIが自動で意味と例文を作ってくれます。")

# 入力は単語だけでOK！
input_word = st.text_input("調べたい単語 (Word):", placeholder="例: meticulous")

# セッション状態（一時的な記憶）を使ってAIの返答を保持します
if "ai_meaning" not in st.session_state:
    st.session_state.ai_meaning = ""
if "ai_memo" not in st.session_state:
    st.session_state.ai_memo = ""

# 🧠 AIに聞くボタン
if st.button("AIに意味と例文を作ってもらう"):
    if input_word:
        with st.spinner("AI先生が考えています..."):
            # AIへの指示（プロンプト）を作成
            prompt_meaning = f"単語「{input_word}」の日本語の意味を、短く1行で教えてください。"
            prompt_memo = f"単語「{input_word}」を使った、日常会話で使える短い英語の例文と、その和訳を1つ作ってください。"
            
            # Geminiにリクエストを送る
            response_meaning = client.models.generate_content(
                model='gemini-2.5-flash', contents=prompt_meaning
            )
            response_memo = client.models.generate_content(
                model='gemini-2.5-flash', contents=prompt_memo
            )
            
            # 結果を画面の記憶に保存
            st.session_state.ai_meaning = response_meaning.text
            st.session_state.ai_memo = response_memo.text
    else:
        st.error("単語を入力してください。")

# AIの返答がすでにある場合は画面に表示
if st.session_state.ai_meaning:
    st.write("---")
    st.subheader("💡 AI先生からの回答")
    st.info(f"**意味:** {st.session_state.ai_meaning}")
    st.success(f"**例文・メモ:**\n{st.session_state.ai_memo}")
    
    # 💾 データベースに保存ボタン
    if st.button("この内容をデータベースに保存する"):
        c.execute(
            "INSERT INTO vocabulary (word, meaning, memo) VALUES (?, ?, ?)",
            (input_word, st.session_state.ai_meaning, st.session_state.ai_memo)
        )
        conn.commit()
        st.success(f"「{input_word}」をマイ単語帳に保存しました！")
        # 保存したら入力欄をリセットするために記憶を消す
        st.session_state.ai_meaning = ""
        st.session_state.ai_memo = ""
        st.rerun()

# ==========================================
# 3. データベース一覧表示
# ==========================================
st.write("---")
st.header("📊 マイ単語帳（保存されたデータ一覧）")

c.execute("SELECT word, meaning, memo FROM vocabulary")
saved_data = c.fetchall()

if saved_data:
    table_data = [{"単語": r[0], "AIが調べた意味": r[1], "AIが作った例文": r[2]} for r in saved_data]
    st.table(table_data)
else:
    st.info("まだ保存された単語はありません。")