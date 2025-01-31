#!/usr/bin/env python
# coding: utf-8
import streamlit as st
import pandas as pd
import google.generativeai as genai
import io

# 事前学習用の会話データ
predefined_conversations = [
    {"customer": "商品はどれくらいの大きさですか？", "store": "【要確認】お問い合わせいただきありがとうございます。メーカーの方に問合せいたしますので今しばらくお待ちください。メーカーより返答があり、大きさは「確認」とのことでした。ご参考いただき購入を検討いただけますと幸いです。どうぞよろしくお願いいたします。"},
    {"customer": "詳細教えて", "store": "【要確認】メーカーより回答がございました。お問い合わせ内容について、下記の回答となります。追加の写真提供は出来かねます。ご希望に添えず誠に申し訳ございません。また何かございましたらお気軽にお問い合わせください。ご検討のほどよろしくお願いいたします。"},
    {"customer": "こちらの商品で〇〇はできますか？", "store": "【要確認】お問い合わせいただきありがとうございます。該当の商品ページは〇〇はできません。ご希望に沿うことが出来ず申し訳ございません。よろしくお願いいたします。"},
   # {"customer": "", "store": ""},
   # {"customer": "", "store": ""},
    {"customer": "サンプル、もしくは、実物の写真見れますか？", "store": "お問い合わせありがとうございます。実物の写真は商品ページの写真が全てとなっております。また何かありましたらお気軽にお問い合わせ下さい。"},
    {"customer": "配送について,いつ届くのか？", "store": "この度は当店をご利用いただきありがとうございます。ご注文商品の配送状況について確認いたしましたところ、〇〇でした。こちらに関しまして当店からのご連絡がなされておらず、誠に申し訳ございません。お手数をおかけし恐縮でございますが、今一度ご確認の程お願い申し上げます。商品が確認できません場合、こちらへとお問い合わせくださいませ。在庫確認後、対応させていただきます。よろしくお願いいたします。"},
    {"customer": "間違いです、キャンセルして下さい。", "store": "【キャンセル対応必要】ご依頼いただきましたご依頼いただきました商品キャンセルの件を承りました。お支払い方法により数日以内に返金処理がなされます。この度は当店をご利用いただきありがとうございました。"},
    {"customer": "返品のお金、いつ返してくれるの？", "store": "【要確認】この度は弊社商品でご迷惑をお掛けして誠に申し訳ございません。返金に関しての処理はすでに弊社では完了しており、カード会社通じての返金となります。たいへんお手数ですが、詳細はカード会社にご連絡いただけますと幸いです。"},
    {"customer": "キャンセル致します。", "store": "【要確認】ご返信くださりありがとうございます。この度は当店をご利用いただいたにも関わらずご迷惑をおかけし大変申し訳ございません。注文のキャンセル・返金処理を承らせていただきました。楽天市場システムの処理タイミングにより、ご請求額との相殺、もしくは翌月からのマイナス請求にて返金処理がなされます。この度は当店をご利用いただきありがとうございました。またのご利用を心よりお待ちしております。"},
    {"customer": "配達はAmazonですか？", "store": "ご連絡いただきありがとうございます。確認いたしましたところ、この度のご注文商品はAmazonマルチチャネルサービスにより配送がなされておりました。お手元の不在票より再配送が可能となっております。何卒よろしくお願いいたします。"},
    {"customer": "再配達の手続きをするようにとメールが届きましたが、不在票が見当たらず伝票番号がわからないため手続き出来ません。", "store": "ご連絡いただきありがとうございます。不在票が確認できないとのことで、誠に申し訳ございません。当店よりメーカーへと確認後、再配送の手配をさせていただきます。ご不便をおかけしており大変恐縮でございますが、商品の到着まで今しばらくお待ちくださいませ。"},
    {"customer": "まだ発送されてないですがいつ頃到着しますか？", "store": "【要確認】おまたせしており大変申し訳ございません。ご注文商品の配送状況を確認いたしましたところ、滞りなければ〇〇の到着予定となっております。現在配送が大変込み合っており、当初のご案内よりお時間を要することとなっておりました。こちらに関してのご連絡が早急になされておらず、誠に申し訳ございません。ご不便をおかけしており大変恐縮でございますが、商品の到着まで今しばらくお待ちくださいませ。"},
    {"customer": "交換したい（店舗都合）", "store": "この度は大変ご迷惑おかけいたしました。商品を返送いただいたうえで対応させていただきます。返品方法はヤマト運輸による集荷とさせていただきますので、集荷の希望日時を以下からご教示いただけますと幸いです。お届け時の状態（付属品やセット入りの場合は全数）で箱、または袋入れのうえ、担当ドライバーにお渡しください。伝票等は不要でございます。【集荷日】ご返信の翌々営業日以降をご指定ください【時間帯】1.8:00-13:00,2.14:00-16:00,3.16:00-18:00,4.17:00-18:30,私共の不手際によりまして多大なるご迷惑をお掛けしておりますこと、重ねて深くお詫び申し上げます。何卒よろしくお願い申し上げます。"},
    {"customer": "商品を頼んだけど全く届かない。", "store": "【要確認】この度は当店をご利用いただきありがとうございます。ご注文商品の配送状況を確認いたしましたところ、配達完了となっておりました。大変お手数ではございますが、ご同居の住民様、配送先住所とあわせて今一度ご確認のほどお願いいたします。すでにご確認いただいており商品の確認が出来ません場合、誤配送などの可能性がございますため、その際はこちらへとお問い合わせくださいませ。在庫確認後対応させていただきます。ご不便をおかけしており大変恐縮でございますが、ご対応のほどよろしくお願いいたします。"},
    {"customer": "商品の到着が遅すぎるのでキャンセルお願いします", "store": "【要確認】お問い合わせありがとうございます。カスタマーサポートでございます。お問い合わせ商品は〇〇に配達完了となっております。今一度お手元に届いていないかご確認いただけますと幸いです。"},
    {"customer": "返品したいです。返品の手順を教えて", "store": "この度は大変ご迷惑おかけいたしました。商品を返送いただいたうえで対応させていただきます。返品方法はヤマト運輸による集荷とさせていただきますので、集荷の希望日時を以下からご教示いただけますと幸いです。お届け時の状態（付属品やセット入りの場合は全数）で箱、または袋入れのうえ、担当ドライバーにお渡しください。伝票等は不要でございます。【集荷日】ご返信の翌々営業日以降をご指定ください【時間帯】1.8:00-13:00,2.14:00-16:00,3.16:00-18:00,4.17:00-18:30,私共の不手際によりまして多大なるご迷惑をお掛けしておりますこと、重ねて深くお詫び申し上げます。何卒よろしくお願い申し上げます。"},
    {"customer": "返金してください。返金の手順を教えて", "store": "この度は大変ご迷惑おかけいたしました。商品を返送いただいたうえで対応させていただきます。返品方法はヤマト運輸による集荷とさせていただきますので、集荷の希望日時を以下からご教示いただけますと幸いです。お届け時の状態（付属品やセット入りの場合は全数）で箱、または袋入れのうえ、担当ドライバーにお渡しください。伝票等は不要でございます。【集荷日】ご返信の翌々営業日以降をご指定ください【時間帯】1.8:00-13:00,2.14:00-16:00,3.16:00-18:00,4.17:00-18:30,私共の不手際によりまして多大なるご迷惑をお掛けしておりますこと、重ねて深くお詫び申し上げます。何卒よろしくお願い申し上げます。"}
    



]


# APIキー、店舗名、担当者名の入力またはExcelアップロード
def get_api_details():
    st.sidebar.header("Gemini APIキー設定")
    api_key = st.sidebar.text_input("APIキーを入力", type="password")
    store_name = st.sidebar.text_input("店舗名を入力")
    manager_name = st.sidebar.text_input("担当者名を入力")
    uploaded_file = st.sidebar.file_uploader("APIキー、店舗名、担当者名の入ったExcelファイルをアップロード", type=["xlsx"])
    
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file, header=None)
        api_key = str(df.iloc[1, 1]).strip()  # B2セル
        store_name = str(df.iloc[2, 1]).strip()  # B3セル
        manager_name = str(df.iloc[3, 1]).strip()  # B4セル
    
    return api_key, store_name, manager_name

# 会話ログの入力（サイドバー）
def get_conversation():
    st.sidebar.header("会話のログ入力")
    customer_1 = st.sidebar.text_area("お客様①")
    store_1 = st.sidebar.text_area("店舗①")
    customer_2 = st.sidebar.text_area("お客様②")
    store_2 = st.sidebar.text_area("店舗②")
    
    return customer_1, store_1, customer_2, store_2

# 返答の作成
def generate_response(api_key, inquiry, context, store_name, manager_name):
    if not api_key:
        return "APIキーが設定されていません。"
    
    introduction = f"{store_name}の{manager_name}です。"
    
    # 事前学習データに基づいた返答を優先
    for convo in predefined_conversations:
        if convo["customer"] in inquiry:
            return f"{introduction} {convo['store']}"
    
    # APIキーを設定
    genai.configure(api_key=api_key)
    
    # Gemini モデルを選択
    model = genai.GenerativeModel("gemini-pro")

    prompt = f"お客様から '{inquiry}' という問い合わせが来ているので、以下の事前学習用データを参考にし、事前学習用データの回答に準じて適切な回答例を作成してください。回答の形式を指定します。【重要度を１から３で判定（１は返答が簡単なもの、２は追加で情報を調べてから返答するもの、３は相談してから返答するもの）】そして、店舗の自己紹介として以下を使用、{introduction} 、その後改行し、回答の生成をお願いします。\n\n事前学習データ:\n{predefined_conversations}"
    
    # 生成を実行
    response = model.generate_content(prompt)
    
    return f" {response.text}"

# メインアプリ
def main():
    st.set_page_config(page_title="問い合わせ対応アプリ")
    st.title("問い合わせ対応アプリ")
    
    api_key, store_name, manager_name = get_api_details()
    
    customer_1, store_1, customer_2, store_2 = get_conversation()
    
    st.header("問い合わせ入力")
    inquiry = st.text_area("お客様からの問い合わせ")
    
    if st.button("問い合わせを処理"):
        context = f"会話履歴: {customer_1}, {store_1}, {customer_2}, {store_2}"
        response = generate_response(api_key, inquiry, context, store_name, manager_name)
        
        st.write(f"### 返答: {response}")
    
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
