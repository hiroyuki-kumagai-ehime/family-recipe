from datetime import datetime
import os
import pandas as pd
import streamlit as st
from google import genai

# ページの基本設定
st.set_page_config(page_title="家族の冷蔵庫・献立アシスタント", page_icon="🍳")

st.title("🍳 家族の冷蔵庫・献立アシスタント")
st.write(
    "冷蔵・冷凍庫の在庫と過去の履歴から、偏りのないメニューをAIが提案します！"
)

# --- サイドバー：APIキーの設定 ---
with st.sidebar:
  st.header("🔑 設定")
  api_key_input = st.text_input(
      "Google Gemini APIキー", type="password", help="Google AI"
                                                " Studioで取得したキーを入力"
  )
  st.markdown("---")
  st.info("アプリのURLを家族のスマホに共有すれば、全員で使えます！")

# CSVファイルの保存パス
HISTORY_FILE = "cooking_history.csv"


def load_history():
  if os.path.exists(HISTORY_FILE):
    return pd.read_csv(HISTORY_FILE)
  else:
    return pd.DataFrame(columns=["日付", "メニュー名", "ジャンル"])


# --- 履歴の読み込みと表示 ---
history_df = load_history()
recent_history_str = "なし"

if not history_df.empty:
  recent_5 = history_df.tail(5)
  recent_history_str = "\n".join([
      f"- {row['日付']}: {row['メニュー名']} ({row['ジャンル']})"
      for _, row in recent_5.iterrows()
  ])

with st.expander("📜 最近作った料理の履歴（直近5件）"):
  st.text(recent_history_str)

# --- 入力フォーム ---
st.subheader("1. 条件の入力")
inventory_text = st.text_area(
    "冷蔵・冷凍庫にある食材",
    "豚肉, キャベツ, 冷凍エビ, 卵, 玉ねぎ, 冷凍うどん",
    help="カンマ区切りで自由に入力してください",
)

col1, col2 = st.columns(2)
with col1:
  portions = st.number_input("何人分？", min_value=1, max_value=10, value=4)
with col2:
  genre_req = st.selectbox(
      "希望のジャンル", ["お任せ", "和食", "中華", "洋食", "時短・簡単"]
  )

# --- 実行ボタン ---
if st.button("🤖 偏りを防ぐレシピを考えてもらう！", type="primary"):
  if not api_key_input:
    st.warning(
        "左側のサイドバーに「Google Gemini"
        " APIキー」を入力してください。"
    )
  elif not inventory_text:
    st.warning("食材を入力してください。")
  else:
    with st.spinner("AIが履歴と在庫を分析してレシピを考えています..."):
      try:
        client = genai.Client(api_key=api_key_input)

        prompt = f"""
                あなたはプロの料理研究家・栄養士です。
                以下の「過去の料理履歴」と「現在の食材」をもとに、栄養や味が偏らない家族向けの美味しいレシピを提案してください。

                【過去の料理履歴（直近で作ったもの）】:
                {recent_history_str}

                【現在の食材】: {inventory_text}
                【作成人数】: {portions}人分
                【要望・ジャンル】: {genre_req}

                【提案時の注意事項】:
                - 過去の料理履歴と主菜の食材（肉・魚など）や味付けが被らないように配慮してください。
                - 偏りを防ぐための簡単なアドバイスを1言添えてください。

                【出力フォーマット】:
                ■ 偏り防止アドバイス:
                ■ メニュー名:
                ■ 選んだジャンル:
                ■ 不足食材 (買い足すべきもの):
                ■ {portions}人分の材料と分量:
                ■ 調理手順:
                """

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )

        st.success("レシピが完成しました！")
        st.markdown(response.text)

        # セッション状態に結果を保持（記録用）
        st.session_state["last_recipe"] = response.text

      except Exception as e:
        st.error(f"エラーが発生しました: {e}")

# --- 食べたものの記録セクション ---
st.markdown("---")
st.subheader("2. 作った料理の記録（履歴に残す）")
with st.form("history_form"):
  recorded_menu = st.text_input(
      "メニュー名（例: 豚とキャベツの味噌炒め）"
  )
  recorded_genre = st.selectbox(
      "ジャンル", ["和食", "中華", "洋食", "その他"]
  )
  submit_button = st.form_submit_button(
      "この料理を履歴に保存する"
  )

  if submit_button:
    if recorded_menu:
      new_row = pd.DataFrame(
          [{
              "日付": datetime.now().strftime("%Y-%m-%d"),
              "メニュー名": recorded_menu,
              "ジャンル": recorded_genre,
          }]
      )
      updated_df = pd.concat([history_df, new_row], ignore_index=True)
      updated_df.to_csv(HISTORY_FILE, index=False, encoding="utf-8-sig")
      st.success(f"✅ 『{recorded_menu}』を履歴に保存しました！")
    else:
      st.warning("メニュー名を入力してください。")