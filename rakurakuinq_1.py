#!/usr/bin/env python
# coding: utf-8
import streamlit as st
import pandas as pd
import google.generativeai as genai

# APIキーの入力またはアップロード
def get_api_key():
    st.sidebar.header("Gemini APIキー設定")
    api_key = st.sidebar.text_input("APIキーを入力", type="password")
    uploaded_file = st.sidebar.file_uploader("APIキーの入ったメモ帳ファイルをアップロード", type=["txt"])
    
    if uploaded_file is not None:
        api_key = uploaded_file.getvalue().decode("utf-8").strip()
    
    return api_key

# 会話ログの入力
def get_conversation():
    st.header("会話のログ入力")
    customer_1 = st.text_area("お客様①")
    store_1 = st.text_area("店舗①")
    customer_2 = st.text_area("お客様②")
    store_2 = st.text_area("店舗②")
    
    return customer_1, store_1, customer_2, store_2

# 重要度判定と問い合わせ分類
def classify_inquiry(inquiry):
    if "急ぎ" in inquiry or "至急" in inquiry:
        importance = "すぐに返信する必要がある"
    elif "確認" in inquiry or "お願いします" in inquiry:
        importance = "返信が必要"
    else:
        importance = "丁寧な返信が必要"
    
    if "注文" in inquiry:
        if "まだ" in inquiry or "前" in inquiry:
            inquiry_type = "注文前の問い合わせ"
        else:
            inquiry_type = "注文後の問い合わせ"
    else:
        inquiry_type = "その他"
    
    return importance, inquiry_type

# 返答の作成
def generate_response(api_key, inquiry, context):
    if not api_key:
        return "APIキーが設定されていません。"
    
    # ここでGemini APIを呼び出す
    response = f"返答の例: {inquiry} に対する適切な返答を作成します。"
    return response

# メインアプリ
def main():
    st.title("問い合わせ対応アプリ")
    
    api_key = get_api_key()
    
    customer_1, store_1, customer_2, store_2 = get_conversation()
    
    st.header("問い合わせ入力")
    inquiry = st.text_area("お客様からの問い合わせ")
    
    if st.button("問い合わせを処理"):
        importance, inquiry_type = classify_inquiry(inquiry)
        context = f"会話履歴: {customer_1}, {store_1}, {customer_2}, {store_2}"
        response = generate_response(api_key, inquiry, context)
        
        st.write(f"### 重要度: {importance}")
        st.write(f"### 問い合わせ分類: {inquiry_type}")
        st.write(f"### 返答: {response}")
    
    st.header("追加情報入力")
    additional_info = st.text_area("追加情報を入力してください")
    
    if st.button("追加情報を考慮して返答を作成"):
        context += f" 追加情報: {additional_info}"
        response = generate_response(api_key, inquiry, context)
        st.write(f"### 修正後の返答: {response}")
    
    # 会話ログのCSV出力
    if st.button("会話ログをCSVで出力"):
        df = pd.DataFrame([
            ["お客様①", customer_1],
            ["店舗①", store_1],
            ["お客様②", customer_2],
            ["店舗②", store_2],
            ["問い合わせ", inquiry],
            ["追加情報", additional_info]
        ], columns=["種類", "内容"])
        df.to_csv("conversation_log.csv", index=False)
        st.success("会話ログがCSVとして出力されました。")
        st.download_button(label="ダウンロード", data=df.to_csv(index=False).encode("utf-8"), file_name="conversation_log.csv", mime="text/csv")

if __name__ == "__main__":
    main()
    
    



