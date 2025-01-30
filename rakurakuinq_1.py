#!/usr/bin/env python
# coding: utf-8
import streamlit as st
import pandas as pd
import google.generativeai as genai
import io

# 事前学習用の会話データ
predefined_conversations = [
    {"customer": "こんにちは、こちらの商品はどれくらいの大きさですか？", "store": "お問い合わせいただきありがとうございます。メーカーの方に問合せいたしますので今しばらくお待ちください。メーカーより返答があり、大きさは「確認」とのことでした。ご参考いただき購入を検討いただけますと幸いです。どうぞよろしくお願いいたします。"},
    {"customer": "tpuケースで、背面のカメラの部分は、カメラを守るために出っ張っているかどうかで、出っ張っていないのをさがしてます", "store": "メーカーより回答がございました。お問い合わせ内容について、下記の回答となります。追加の写真提供は出来かねます。ご希望に添えず誠に申し訳ございません。また何かございましたらお気軽にお問い合わせください。ご検討のほどよろしくお願いいたします。"},
    {"customer": "こちらの商品で〇〇はできますか？", "store": "お問い合わせいただきありがとうございます。該当の商品ページは〇〇はできません。ご希望に沿うことが出来ず申し訳ございません。よろしくお願いいたします。"},
    {"customer": "はじめましてソーラーパネルとポタ電　他メーカー同士のものをつなげたくてこちらに行きつきました。ソーラー充電ケーブルMC4からXT60ポートケーブルを探していました。XT60と反対側の方に2つついているのですが、なぜ2つあるのでしょうか？片方がMC4で、もう一つはなんですか？まったく機械に弱いので教えて下さい。", "store": "商品についてのご質問ありがとうございます。私どもは販売業者のため、商品の詳しい仕様については把握できかねます。そのため、今回はメーカーに問い合わせ処理をさせていただきました。返信があり次第、改めてご連絡させていただきますので、いましばらくお待ちくださいませ。よろしくお願いいたします。"},
    {"customer": "白色は有りませんか？", "store": "お問い合わせありがとうございます。商品の白黒はお取り扱いがございません。また何かございましたらお気軽にお問い合わせ下さいませ。"},
    {"customer": "こちら、サンプル、もしくは、実物の写真見れますか？", "store": "お問い合わせありがとうございます。実物の写真は商品ページの写真が全てとなっております。また何かありましたらお気軽にお問い合わせ下さい。"},
    {"customer": "配送について,いつ届くのか？", "store": "この度は当店をご利用いただきありがとうございます。ご注文商品の配送状況について確認いたしましたところ、〇〇でした。こちらに関しまして当店からのご連絡がなされておらず、誠に申し訳ございません。お手数をおかけし恐縮でございますが、今一度ご確認の程お願い申し上げます。商品が確認できません場合、こちらへとお問い合わせくださいませ。在庫確認後、対応させていただきます。よろしくお願いいたします。"},
    {"customer": "キャンセルしたい。間違いです、キャンセルして下さい。", "store": "ご依頼いただきました商品キャンセルの件を承りました。お支払い方法により数日以内に返金処理がなされます。この度は当店をご利用いただきありがとうございました。"},
    {"customer": "返品のお金、いつ返してくれるの？", "store": "この度は弊社商品でご迷惑をお掛けして誠に申し訳ございません。返金に関しての処理はすでに弊社では完了しており、カード会社通じての返金となります。たいへんお手数ですが、詳細はカード会社にご連絡いただけますと幸いです。"},
    {"customer": "出荷できないとの連絡を頂きましたのでキャンセル致します。", "store": "ご返信くださりありがとうございます。この度は当店をご利用いただいたにも関わらずご迷惑をおかけし大変申し訳ございません。注文のキャンセル・返金処理を承らせていただきました。楽天市場システムの処理タイミングにより、ご請求額との相殺、もしくは翌月からのマイナス請求にて返金処理がなされます。この度は当店をご利用いただきありがとうございました。またのご利用を心よりお待ちしております。"},
    {"customer": "配達はAmazonですか？身の覚えのない再配達の紙が入っててこちらの商品がAmazonできたのかなと思いご連絡いました", "store": "ご連絡いただきありがとうございます。確認いたしましたところ、この度のご注文商品はAmazonマルチチャネルサービスにより配送がなされておりました。お手元の不在票より再配送が可能となっております。何卒よろしくお願いいたします。"},
    {"customer": "再配達の手続きをするようにとメールが届きましたが、不在票が見当たらず伝票番号がわからないため手続き出来ません。", "store": "ご連絡いただきありがとうございます。不在票が確認できないとのことで、誠に申し訳ございません。当店よりメーカーへと確認後、再配送の手配をさせていただきます。ご不便をおかけしており大変恐縮でございますが、商品の到着まで今しばらくお待ちくださいませ。"},
    {"customer": "まだ発送されてないですがいつ頃到着しますか？よろしくお願いします。", "store": "おまたせしており大変申し訳ございません。ご注文商品の配送状況を確認いたしましたところ、滞りなければ〇〇の到着予定となっております。現在配送が大変込み合っており、当初のご案内よりお時間を要することとなっておりました。こちらに関してのご連絡が早急になされておらず、誠に申し訳ございません。ご不便をおかけしており大変恐縮でございますが、商品の到着まで今しばらくお待ちくださいませ。"},
    {"customer": "交換したい（店舗都合）交換の理由：頼んだ商品と違います。頼んだのは40センチなのにこれは30センチみたいな感じだし色も違う。", "store": "この度は大変ご迷惑おかけいたしました。商品を返送いただいたうえで対応させていただきます。返品方法はヤマト運輸による集荷とさせていただきますので、集荷の希望日時を以下からご教示いただけますと幸いです。お届け時の状態（付属品やセット入りの場合は全数）で箱、または袋入れのうえ、担当ドライバーにお渡しください。伝票等は不要でございます。【集荷日】ご返信の翌々営業日以降をご指定ください【時間帯】1.8:00-13:00,2.14:00-16:00,3.16:00-18:00,4.17:00-18:30,私共の不手際によりまして多大なるご迷惑をお掛けしておりますこと、重ねて深くお詫び申し上げます。何卒よろしくお願い申し上げます。"},
    {"customer": "商品を頼んだけど全く届かない。どうなっていますか？", "store": "この度は当店をご利用いただきありがとうございます。ご注文商品の配送状況を確認いたしましたところ、配達完了となっておりました。大変お手数ではございますが、ご同居の住民様、配送先住所とあわせて今一度ご確認のほどお願いいたします。すでにご確認いただいており商品の確認が出来ません場合、誤配送などの可能性がございますため、その際はこちらへとお問い合わせくださいませ。在庫確認後対応させていただきます。ご不便をおかけしており大変恐縮でございますが、ご対応のほどよろしくお願いいたします。"},
    {"customer": "商品の到着が遅すぎるのでキャンセルお願いします", "store": "お問い合わせありがとうございます。カスタマーサポートでございます。お問い合わせ商品は〇〇に配達完了となっております。今一度お手元に届いていないかご確認いただけますと幸いです。"},
    {"customer": "届いてすぐに壊れたので、返品したいです。返品の手順を教えて", "store": "この度は大変ご迷惑おかけいたしました。商品を返送いただいたうえで対応させていただきます。返品方法はヤマト運輸による集荷とさせていただきますので、集荷の希望日時を以下からご教示いただけますと幸いです。お届け時の状態（付属品やセット入りの場合は全数）で箱、または袋入れのうえ、担当ドライバーにお渡しください。伝票等は不要でございます。【集荷日】ご返信の翌々営業日以降をご指定ください【時間帯】1.8:00-13:00,2.14:00-16:00,3.16:00-18:00,4.17:00-18:30,私共の不手際によりまして多大なるご迷惑をお掛けしておりますこと、重ねて深くお詫び申し上げます。何卒よろしくお願い申し上げます。"}
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

    prompt = f"{introduction} お客様から '{inquiry}' という問い合わせが来ているので、以下の事前学習用の会話データを参考にしながら適切な回答例を作成してください。回答の生成が難しい場合は、文頭に【要確認】と表示してください。\n\n事前学習データ:\n{predefined_conversations}\n\n問い合わせ内容:\n{inquiry}"
    
    # 生成を実行
    response = model.generate_content(prompt)
    
    return f"{introduction} {response.text}"

# メインアプリ
def main():
    st.title("問い合わせ対応アプリ")
    
    api_key, store_name, manager_name = get_api_details()
    
    customer_1, store_1, customer_2, store_2 = get_conversation()
    
    st.header("問い合わせ入力")
    inquiry = st.text_area("お客様からの問い合わせ")
    
    if st.button("問い合わせを処理"):
        context = f"会話履歴: {customer_1}, {store_1}, {customer_2}, {store_2}"
        response = generate_response(api_key, inquiry, context, store_name, manager_name)
        
        st.write(f"### 返答: {response}")
    
    st.header("追加情報入力")
    additional_info = st.text_area("追加情報を入力してください")
    
    if st.button("追加情報を考慮して返答を作成"):
        if 'context' not in locals():
            context = ""
        context += f" 追加情報: {additional_info}"
        response = generate_response(api_key, inquiry, context, store_name, manager_name)
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
