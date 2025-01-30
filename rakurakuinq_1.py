#!/usr/bin/env python
# coding: utf-8
import streamlit as st
import pandas as pd
import google.generativeai as genai
import io

# 事前学習用の会話データ
predefined_conversations = [
    {"customer": "注文した商品が届かないのですが？", "store": "ご注文番号を教えていただけますか？確認いたします。"},
    {"customer": "返品は可能ですか？", "store": "はい、商品到着後7日以内であれば返品可能です。"},
    {"customer": "営業時間を教えてください。", "store": "当店の営業時間は10:00～19:00です。"}
]

# APIキーの入力またはアップロード
def get_api_key():
    st.sidebar.header("Gemini APIキー設定")
    api_key = st.sidebar.text_input("APIキーを入力", type="password")
    uploaded_file = st.sidebar.file_uploader("APIキーの入ったメモ帳ファイルをアップロード", type=["txt"])
    
    if uploaded_file is not None:
        api_key = uploaded_file.getvalue().decode("utf-8").strip()
    
    return api_key

# 会話ログの入力（サイドバー）
def get_conversation():
    st.sidebar.header("会話のログ入力")
    customer_1 = st.sidebar.text_area("お客様①")
    store_1 = st.sidebar.text_area("店舗①")
    customer_2 = st.sidebar.text_area("お客様②")
    store_2 = st.sidebar.text_area("店舗②")
    
    return customer_1, store_1, customer_2, store_2

# 重要度判定と問い合わせ分類（Gemini AIを使用）
def classify_inquiry(api_key, inquiry):
    if not api_key:
        return "APIキーが設定されていません。", "分類できません"
    
    # APIキーを設定
    genai.configure(api_key=api_key)
    
    # Gemini モデルを選択
    model = genai.GenerativeModel("gemini-pro")
    
    # プロンプト作成
    prompt = f"""
    以下の問い合わせの重要度を判定し、分類してください。

    問い合わせ: "{inquiry}"

    重要度は以下の3つの中から選択してください。
    1. すぐに返信する必要がある
    2. 返信が必要
    3. 丁寧な返信が必要

    また、問い合わせの種類は以下の3つの中から選択してください。
    1. 注文前の問い合わせ
    2. 注文後の問い合わせ
    3. その他

    重要度と問い合わせの種類を出力してください。
    """
    
    # Gemini API に問い合わせる
    response = model.generate_content(prompt)
    
    # 結果を解析（応答テキストの抽出）
    result = response.text.strip().split("\n")
    
    if len(result) >= 2:
        importance = result[0].strip()
        inquiry_type = result[1].strip()
    else:
        importance, inquiry_type = "分類エラー", "分類エラー"

    return importance, inquiry_type

# 返答の作成
def generate_response(api_key, inquiry, context):
    if not api_key:
        return "APIキーが設定されていません。"
    
    # APIキーを設定
    genai.configure(api_key=api_key)
    
    # Gemini モデルを選択
    model = genai.GenerativeModel("gemini-pro")

    prompt = f"お客様から '{inquiry}' という問い合わせが来ているので、以下の会話履歴、問い合わせ内容、既存の返答内容を考慮して回答例を作成してください。\n\n会話履歴:\n{context}\n\n問い合わせ内容:\n{inquiry}"
    
    # 生成を実行
    response = model.generate_content(prompt)
    
    return response.text

# メインアプリ
def main():
    st.title("問い合わせ対応アプリ")
    
    api_key = get_api_key()
    
    customer_1, store_1, customer_2, store_2 = get_conversation()
    
    st.header("問い合わせ入力")
    inquiry = st.text_area("お客様からの問い合わせ")
    
    if st.button("問い合わせを処理"):
        importance, inquiry_type = classify_inquiry(api_key, inquiry)
        context = f"会話履歴: {customer_1}, {store_1}, {customer_2}, {store_2}"
        response = generate_response(api_key, inquiry, context)
        
        st.write(f"### 重要度: {importance}")
        st.write(f"### 問い合わせ分類: {inquiry_type}")
        st.write(f"### 返答: {response}")
    
    st.header("追加情報入力")
    additional_info = st.text_area("追加情報を入力してください")
    
    if st.button("追加情報を考慮して返答を作成"):
        if 'context' not in locals():
            context = ""
        context += f" 追加情報: {additional_info}"
        response = generate_response(api_key, inquiry, context)
        st.write(f"### 修正後の返答: {response}")
    
    # 会話ログのExcel出力
    if st.button("会話ログをExcelで出力"):
        df = pd.DataFrame([
            ["お客様①", customer_1],
            ["店舗①", store_1],
            ["お客様②", customer_2],
            ["店舗②", store_2],
            ["問い合わせ", inquiry],
            ["追加情報", additional_info]
        ], columns=["種類", "内容"])
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="会話ログ")
        output.seek(0)
        
        st.success("会話ログがExcelとして出力されました。")
        st.download_button(label="ダウンロード", data=output, file_name="conversation_log.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

if __name__ == "__main__":
    main()

