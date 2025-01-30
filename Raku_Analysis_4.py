#!/usr/bin/env python
# coding: utf-8
import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import requests
import time
import openpyxl  # Excelファイルを操作するために必要
import matplotlib.pyplot as plt
import japanize_matplotlib
import io
from io import StringIO, BytesIO
import re
import base64
from email import message_from_bytes
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import json
import datetime
import plotly.express as px
import os
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome import service as fs
from selenium.webdriver import ChromeOptions
import keepa
import re



SCOPES = ['https://mail.google.com/']
credentialPath = 'auth_raku.json'
tokenPath = 'raku_token.json'


# アプリのタイトルを設定
st.set_page_config(page_title="Raku Analysis")

# セッション状態の初期化
if 'login' not in st.session_state:
    st.session_state['login'] = False

# Gmail APIの初期化関数を修正
def gmail_init():
    service = st.session_state['service']
    
    df = pd.DataFrame(columns=['氏名', '配送方法', '配送番号'])
    with st.form("email_search"):
        start_date = st.date_input("開始日を選択してください")
        end_date = st.date_input("終了日を選択してください")
        submit_button = st.form_submit_button("メール検索")
    if submit_button:
        messages = []

        while start_date <= end_date:
            query = f'subject:"点が発送されました" after:{start_date.strftime("%Y/%m/%d")} before:{(start_date + datetime.timedelta(days=1)).strftime("%Y/%m/%d")}'
            page_token = None

            while True:
                response = service.users().messages().list(userId='me', q=query, maxResults=500, pageToken=page_token).execute()
                if 'messages' in response:
                    messages.extend(response['messages'])

                page_token = response.get('nextPageToken')
                if not page_token:
                    break

            start_date += datetime.timedelta(days=1)


        for message in messages:
#             msg = service.users().messages().get(userId='me', id=message['id']).execute()
            msg = service.users().messages().get(userId='me', id=message['id'], format='full').execute()
            payload = msg['payload']
            headers = payload['headers']
            for part in payload['parts']:
                if part['mimeType'] == 'text/html':
                    body = part['body']['data']
                    body = base64.urlsafe_b64decode(body).decode('utf-8')

                    try:
                        # 元の注文番号の取得ロジック
                        order_name = str(body.split("<p> <strong> ")[1].split(", <br />")[0])
                        if len(order_name) >= 100:  # 注文番号が100文字以上の場合
                            order_name = '配送先なし'  # '配送先なし'に置き換える
                    except IndexError:
                        try:
                            # 新しい注文者名の取得ロジック
                            start_marker = 'お届け先:</span> <span class="rio_sc_jp_label_value" style="color: rgb(15, 17, 17); font-size: 15px; line-height: 20px; font-weight: bold; display: block; font-family: &quot;Amazon Ember&quot;, Arial, sans-serif; font-style: normal; margin: 0; padding: 0; border: 0; outline: 0; vertical-align: baseline"> '
                            end_marker = ', <br />'
                            start_idx = body.index(start_marker) + len(start_marker)
                            end_idx = body.index(end_marker, start_idx)
                            order_name = body[start_idx:end_idx].strip()  # 名前のみを抽出
                        except (IndexError, ValueError):
                            order_name = "注文者名が見つかりません"

                    print(order_name)

                    # 配送方法の取得 (修正を加える)
                    try:
                        delivery_method = str(body.split("ご注文商品は")[1].split("でお届けいたします")[0])
                        if len(delivery_method) > 100:
                            delivery_method = "Amazon"
                    except IndexError:
                        delivery_method = "配送方法が見つかりません"
                    print(delivery_method)

                    # 配送番号の取得 (修正を加える)
                    try:
                        tracking_number = str(body.split("お問い合わせ伝票番号は")[1].split("です。")[0])
                    except IndexError:
                        tracking_number = "配送番号が見つかりません"
                    # Amazonはこれでとれそう
                    print(tracking_number)


            # 取得した情報をDataFrameに追加する
            new_row  = pd.DataFrame({'氏名': [order_name], '配送方法': [delivery_method], '配送番号': [tracking_number]})
            if df.empty:
                df = new_row  # 初めての行なので、df に new_row を代入する
            else:
                df = df.append(new_row, ignore_index=True)
            
                        
        st.write(df)
        csv = df.to_csv(index=False)
        st.download_button(
            label="データをダウンロード",  # ボタンのラベル
            data=csv,  # ダウンロードするコンテンツ
            file_name='haisoubangou.csv',  # ダウンロードされるファイルの名前
            mime='text/csv',  # MIMEタイプ（この場合はCSVファイル）
        )
        


            

                




def main():  
    # ログインチェック
    if not st.session_state['login']:
        col1, col2 = st.columns(2)

        with col1:
            st.image("Banner_Raku_Analysis.png")

        with col2:
            st.title("認証")
            if st.button("認証開始", key="login_button"):
                flow = InstalledAppFlow.from_client_secrets_file(credentialPath, SCOPES, redirect_uri='urn:ietf:wg:oauth:2.0:oob')
                authorization_url, _ = flow.authorization_url(prompt='consent')
                st.session_state['auth_url'] = authorization_url
                st.session_state['flow'] = flow

            if st.session_state.get('auth_url'):
                st.write(f'以下のURLにアクセスして認証を完了してください: [ここをクリック]({st.session_state["auth_url"]})')
                auth_code = st.text_input('認証コードをこちらに入力してください:')

                if st.button('認証', key="auth_button") and auth_code:
                    flow = st.session_state['flow']
                    flow.fetch_token(code=auth_code)
                    creds = flow.credentials
                    with open('raku_token.json', 'w') as token:
                        token.write(creds.to_json())
                    creds = Credentials.from_authorized_user_file(tokenPath, SCOPES)
                    service = build('gmail', 'v1', credentials=creds)
                    st.session_state['service'] = service
                    st.session_state['creds'] = creds
                    st.session_state['login'] = True
                    del st.session_state['auth_url']  # 認証URLのセッション状態を削除
                    st.rerun()
    else:
        # サイドバーでページの選択肢を表示
        st.sidebar.image("Banner_Raku_Analysis2.png")
        st.sidebar.success("ログイン成功")
        page = st.sidebar.selectbox('モード選択', ['Raku_OSM',"Raku_発送"])#"Raku_Add","Raku_CONC",'Raku_PV_Research',"楽天リサーチ","ASIN解析"
        st.sidebar.title("Raku_OSM")
        st.sidebar.text("Gmailから配送番号を取得")
        st.sidebar.title("Raku_発送")
        st.sidebar.text("楽天用発送番号作成")
        st.sidebar.title("Raku_CONC")
        st.sidebar.text("Keepaファイル結合")
        st.sidebar.title("Raku_PV_Research")
        st.sidebar.text("PV分析ツール")
        st.sidebar.title("楽天リサーチ")
        st.sidebar.text("楽天とKeepaで商品検索")
        st.sidebar.title("ASIN解析")
        st.sidebar.text("ASIN-SellerID解析")
#         st.sidebar.title("Raku_Add")
#         st.sidebar.text("【ローカル限定】Amazon住所入力/削除ツール")
        

        # ホームページの内容
        if page == 'Raku_OSM':
            st.title("Raku_OSM")
            gmail_init()
            


        elif page == 'Raku_発送':
            st.title("Raku_発送")
            uploaded_file =st.file_uploader("配送番号ファイルを選択してください", type=['csv'],key="file1")
            uploaded_file_2 = st.file_uploader("楽天注文情報ファイルを選択してください", type=['csv'], key="file2")
            if uploaded_file is not None and uploaded_file_2 is not None:
                delivery_numbers_df = pd.read_csv(uploaded_file,usecols=['氏名', '配送方法', '配送番号'], encoding="utf-8",on_bad_lines='skip')
                orders_df = pd.read_csv(uploaded_file_2, usecols=['ステータス', '注文番号', '送付先ID', '発送完了報告日時', '送付先姓', '送付先名'], encoding='shift_jis')
                
                #orders_dfを処理します
                orders_df['発送完了報告日'] = pd.to_datetime(orders_df['発送完了報告日時']).dt.strftime('%Y-%m-%d')
                orders_df['氏名'] = orders_df['送付先姓'] + ' ' + orders_df['送付先名']
                orders_df.drop(['送付先姓', '送付先名'], axis=1, inplace=True)
                duplicates_df = orders_df.copy()  # ここで.copy()を使います

                # "ステータス"列が「900」のものを除外します。
                duplicates_df = duplicates_df[duplicates_df['ステータス'] != 900]

                # "注文番号"列から「-」と「-」で挟まれている文字列を抜き出し、「注文日」という新しい列を作成します。
                duplicates_df['注文日'] = duplicates_df['注文番号'].str.extract('-(.*?)-')

                # "注文番号"列で重複する行を削除します。
                duplicates_df = duplicates_df.drop_duplicates(subset='注文番号', keep='first')

                duplicates_df = duplicates_df[duplicates_df.duplicated(['氏名'], keep=False)]

                if not duplicates_df.empty:
                    st.title("重複する名前の注文")
                    st.write(duplicates_df)
                    
                combined_df = pd.merge(delivery_numbers_df, orders_df, on='氏名')
                combined_df['発送明細ID'] = ''
                combined_df.rename(columns={'配送番号': 'お荷物伝票番号', '配送方法': '配送会社', '発送完了報告日時': '発送日'}, inplace=True)
                combined_df['配送会社'].replace({'Amazon': '1000', 'ヤマト運輸': '1001', '日本郵便': '1003'}, inplace=True)
                combined_df.loc[combined_df['配送会社'].str.contains('日本郵便'), '配送会社'] = '1003'
                today = datetime.datetime.now().strftime('%Y-%m-%d')
                combined_df['発送日']  = combined_df['発送日'].fillna(today)
                combined_df = combined_df[combined_df['発送日'] == today]
                combined_df['発送日'] = pd.to_datetime(combined_df['発送日']).dt.strftime('%Y-%m-%d')
                combined_df['発送日'] = combined_df['発送日'].astype(str)
                combined_df.loc[combined_df['配送会社'].str.len() >= 100, '配送会社'] = '1000'
                column_order = ['注文番号', '送付先ID', '発送明細ID', 'お荷物伝票番号', '配送会社', '発送日']
                combined_df = combined_df.reindex(columns=column_order)
                
                csv = combined_df.to_csv(index=False, encoding='shift_jis')
                
                st.download_button(
                    label="発送番号をダウンロード",  # ボタンのラベル
                    data=csv,  # ダウンロードするコンテンツ
                    file_name='hassoubangou.csv',  # ダウンロードされるファイルの名前
                    mime='text/csv',  # MIMEタイプ（この場合はCSVファイル）
                )
        elif page == 'Raku_CONC':
            st.title("Raku_CONC")
            # ファイルアップロードセクション
            uploaded_files = st.file_uploader("Keepaファイル読み込み", accept_multiple_files=True, type=['xlsx', 'csv'])

            if uploaded_files:
                # アップロードされたファイルを結合して1つのデータフレームに読み込む
                dfs = []
                for uploaded_file in uploaded_files:
                    # ExcelファイルとCSVファイルの両方を処理できるようにする
                    if uploaded_file.name.endswith('.xlsx'):
                        df = pd.read_excel(uploaded_file)
                    else:
                        df = pd.read_csv(uploaded_file)
                    dfs.append(df)
                combined_df = pd.concat(dfs)

                # 以降のデータ処理
                selected_columns = ['ASIN', 'Title', 'Reviews: Rating', 'Categories: Root', 'Categories: Sub', 'Brand', 'Package: Dimension (cm³)', 'Buy Box Seller']
                combined_df['Buy Box Seller ID'] = combined_df['Buy Box Seller'].str.extract(r'%\s*(.*?)\)')
                combined_df.drop_duplicates(subset='ASIN', inplace=True)
                combined_df.sort_values(by='Categories: Root', ascending=True, inplace=True)
                combined_df = combined_df[selected_columns + ['Buy Box Seller ID']]

                # Streamlitアプリ上にデータを表示
                st.dataframe(combined_df)

                # データをExcelファイルとしてダウンロードするためのボタン
                towrite = io.BytesIO()
                downloaded_file = combined_df.to_excel(towrite, encoding='utf-8', index=False, header=True)  # Excelファイルとして書き込む
                towrite.seek(0)  # ファイルポインタを先頭に戻す
                st.download_button(label="Excelファイルとしてダウンロード", data=towrite, file_name="Raku_CONC.xlsx", mime="application/vnd.ms-excel")
        elif page == 'Raku_PV_Research':
            # PVファイル読み込み
            st.title("Raku_PV_Research")
            uploaded_files_pv = st.file_uploader("PVファイル読み込み", accept_multiple_files=True, type=['xlsx', 'csv'])

            if uploaded_files_pv:
                dfs_pv = []
                for uploaded_file in uploaded_files_pv:
                    if uploaded_file.name.endswith('.xlsx'):
                        df = pd.read_excel(uploaded_file, skiprows=5, dtype={"アクセス人数": object}, error_bad_lines=False, warn_bad_lines=True)
                    else:
                        df = pd.read_csv(uploaded_file, skiprows=5, dtype={"アクセス人数": object}, error_bad_lines=False, warn_bad_lines=True)

                    df = df[df["アクセス人数"] != "0.00%"]
                    df["アクセス人数"] = df["アクセス人数"].astype(int)
                    dfs_pv.append(df)

                df_pv = pd.concat(dfs_pv)

                # `商品管理番号`でグループ化し、`アクセス人数`は合計、他の列は最初の値を取得
                aggregation_functions = {col: 'first' for col in df_pv.columns}
                aggregation_functions['アクセス人数'] = 'sum'  # `アクセス人数`だけ合計する
                df_pv = df_pv.groupby('商品管理番号', as_index=False).agg(aggregation_functions)
                # ジャンル列を'>'で区切り、最初の部分を新たなジャンル列として設定
                df_pv['ジャンル'] = df_pv['ジャンル'].str.split('>').str[0]


                st.write(df_pv)

            # RMS商品情報読み込み
            uploaded_file_rms = st.file_uploader("RMS商品情報読み込み", type=['xlsx', 'csv'])

            if uploaded_file_rms:
                if uploaded_file_rms.name.endswith('.xlsx'):
                    df_rms = pd.read_excel(uploaded_file_rms, error_bad_lines=False, warn_bad_lines=True)
                else:
                    df_rms = pd.read_csv(uploaded_file_rms,encoding='shift_jis', error_bad_lines=False, warn_bad_lines=True)

                df_rms["ASIN"] = df_rms["商品管理番号（商品URL）"].apply(lambda x: x.split("-")[1].upper() if isinstance(x, str) and len(x.split("-")) > 1 else "")

            # 両データフレームの結合
            if uploaded_files_pv and uploaded_file_rms:
                merged_df = pd.merge(df_rms, df_pv, left_on="商品管理番号（商品URL）", right_on="商品管理番号", how="left")
                merged_df = merged_df.dropna(subset=['SKU管理番号'])
                # 'アクセス人数'列の欠損値を0で補完
                merged_df['アクセス人数'] = merged_df['アクセス人数'].fillna(0)
                # アクセス人数を降順で並び替え
                sorted_df = merged_df.sort_values("アクセス人数", ascending=False)

                # 必要な列だけを残す
                columns_to_keep = ["ASIN", "商品管理番号（商品URL）","商品管理番号","商品名", "販売価格",  "売上", 
                                   "売上件数", "売上個数", "アクセス人数", "ユニークユーザー数", "未購入アクセス人数", 
                                   "お気に入り登録ユーザ数", "お気に入り総ユーザ数",'レビュー投稿数','ジャンル']
                sorted_df = sorted_df[columns_to_keep]
                sorted_df['ジャンル'] = sorted_df['ジャンル'].fillna('ジャンルなし')
                st.dataframe(sorted_df)
                
                # 必要な列を抽出し、アクセス人数が0でない行をフィルタリング
                delete_asin_df = sorted_df[['ASIN', '商品管理番号（商品URL）', '販売価格', 'アクセス人数']]
                delete_asin_df = delete_asin_df[delete_asin_df['アクセス人数'] == 0]

                # CSV形式に変換
                csv = delete_asin_df.to_csv(index=False).encode('utf-8-sig')

                # ダウンロードボタンを作成
                st.download_button(
                    label="アクセス人数0のASINをダウンロード",
                    data=csv,
                    file_name='delete_asin_data.csv',
                    mime='text/csv'
                )
                
                
                
                st.title("データ分析")
                ## X軸とY軸の列名を指定
                x_axis = "アクセス人数"
                y_axis = "売上"

                # 散布図を作成し、回帰直線を追加
                fig = px.scatter(sorted_df, x=x_axis, y=y_axis, color="ジャンル",
                                 hover_data=[x_axis, y_axis, "ジャンル"],
                                 labels={"ジャンル": "ジャンル", x_axis: "アクセス人数", y_axis: "売上"},
                                 trendline="ols"# 回帰直線を追加
                                                    )  

                # グラフのタイトルを設定
                fig.update_layout(title="アクセス人数と売上の関連")

                # インタラクティブなグラフを表示
                st.plotly_chart(fig)
                
                
                
                
                
                # X軸の列名を指定
                x_axis = '販売価格'

                # Y軸の選択肢（数値列のみを選択肢とする）
                y_options = sorted_df.select_dtypes(include=[np.number]).columns.tolist()
                y_options.remove(x_axis)  # X軸に使用している列は選択肢から除外
                # "アクセス人数"のインデックスを取得
                default_index = y_options.index("アクセス人数")

                # ユーザーにY軸を選択させる
                y_axis = st.selectbox('Y軸を選択してください:', y_options, index=default_index)

                # 利用可能なジャンルのリストを取得
                available_genres = sorted_df['ジャンル'].unique().tolist()

                # マルチセレクトウィジェットを使用してジャンルを選択
                selected_genres = st.multiselect('表示するジャンルを選択してください:',
                                                  options=available_genres,
                                                  default=available_genres[0])

                # 選択されたジャンルに基づいてデータフレームをフィルタリング
                filtered_df = sorted_df[sorted_df['ジャンル'].isin(selected_genres)]

                # 散布図を作成
                fig = px.scatter(filtered_df, x=x_axis, y=y_axis, color='ジャンル', hover_data=[x_axis, y_axis, 'ジャンル'],trendline="ols")
                
                fig.update_layout(title="販売価格との関連")

                # インタラクティブなグラフを表示
                st.plotly_chart(fig)
                
        elif page =="Raku_Add":
            st.title("Raku_Add")
            options = ChromeOptions()
            # option設定を追加
#             options.add_argument("--headless")
#             options.add_argument('--window-size=1920,1080')
            # option設定を追加（設定する理由はメモリの削減）
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')

            # テキスト入力ウィジェットでEメールアドレスとパスワードを受け取る
            email = st.text_input("Amazonログインアドレスを入力してください")
            password = st.text_input("Amazonパスワードを入力してください", type="password")
            if email and password:
                seconds = st.slider("Amazonログイン時に待機する秒数を選択してください", min_value=0, max_value=100, value=30)
                # 選択された秒数を表示
                st.write(f"選択された秒数: {seconds}秒")
                st.title("住所入力")
                uploaded_file = st.file_uploader("RMS注文情報を選択してください", type=["csv"])
                if uploaded_file is not None:
                    # CSVファイルを読み込む
                    address_data = pd.read_csv(uploaded_file, encoding="shift_jis")
                    # 結果を表示
                    st.write("注文情報：",address_data)
                    if st.button("入力開始"):
                        driver = webdriver.Chrome(options=options)
                        driver.get("https://www.amazon.co.jp/ap/signin?openid.pape.max_auth_age=0&openid.return_to=https%3A%2F%2Fwww.amazon.co.jp%2F%3Fref_%3Dnav_signin&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.assoc_handle=jpflex&openid.mode=checkid_setup&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0&")
                        time.sleep(seconds)

                        email_input = driver.find_element(By.XPATH, '//*[@id="ap_email"]')
                        email_input.send_keys(email)
                        driver.find_element(By.XPATH, '//*[@id="continue"]').click()
                        time.sleep(2)

                        password_input = driver.find_element(By.XPATH, '//*[@id="ap_password"]')
                        password_input.send_keys(password)
                        driver.find_element(By.XPATH, '//*[@id="signInSubmit"]').click()
                        time.sleep(seconds)
                        try:
                            driver.get("https://www.amazon.co.jp/a/addresses")
                            st.text("Amazonサインイン成功")
                            wait = WebDriverWait(driver, 10)
                            element = WebDriverWait(driver, 10).until( EC.element_to_be_clickable((By.XPATH, '//*[@id="ya-myab-plus-address-icon"]')))
                            element.click()
                        except Exception as e:
                            st.error(f"エラーが発生しましたので、Amazonにサインインできるか試行してから再実行してください。https://www.amazon.co.jp/ap/signin?openid.pape.max_auth_age=900&openid.return_to=https%3A%2F%2Fwww.amazon.co.jp%2Fgp%2Fyourstore%2Fhome%3Fpath%3D%252Fgp%252Fyourstore%252Fhome%26useRedirectOnSuccess%3D1%26signIn%3D1%26action%3Dsign-out%26ref_%3Dnav_AccountFlyout_signout&openid.assoc_handle=jpflex&openid.mode=checkid_setup&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0: {e}")
                        time.sleep(2)
                        for index, row in address_data.iterrows():

                            # 住所情報の入力処理をここに記述してください。
                            full_name = row['送付先姓'] + ' ' + row['送付先名']
                            number = str(row['送付先電話番号1']) 

                            if len(number) == 2:
                                number = '0' + number  # 2桁の場合、先頭に0を追加
                            elif len(number) == 1:
                                number = '0' + number  # 1桁の場合、0を2個追加


                            phone_number = number + str(row['送付先電話番号2']) + str(row['送付先電話番号3'])
                            postal_code1 = str(row['送付先郵便番号1']).zfill(3)
                            postal_code2 = str(row['送付先郵便番号2']).zfill(4)

                            driver.find_element(By.XPATH, '//*[@id="address-ui-widgets-enterAddressFullName"]').send_keys(full_name)
                            driver.find_element(By.XPATH, '//*[@id="address-ui-widgets-enterAddressPhoneNumber"]').send_keys(phone_number)

                            try:
                                driver.find_element(By.XPATH, '//*[@id="address-ui-widgets-enterAddressPostalCode"]').clear()
                                driver.find_element(By.XPATH, '//*[@id="address-ui-widgets-enterAddressPostalCode"]').send_keys(postal_code1+postal_code2)
                            except:
                                driver.find_element(By.XPATH, '//*[@id="address-ui-widgets-enterAddressPostalCodeOne"]').clear()
                                driver.find_element(By.XPATH, '//*[@id="address-ui-widgets-enterAddressPostalCodeOne"]').send_keys(postal_code1)
                                driver.find_element(By.XPATH, '//*[@id="address-ui-widgets-enterAddressPostalCodeTwo"]').clear()
                                driver.find_element(By.XPATH, '//*[@id="address-ui-widgets-enterAddressPostalCodeTwo"]').send_keys(postal_code2)


                    #都道府県を選択するコード：
                    #         select = Select(driver.find_element(By.XPATH, '//*[@id="address-ui-widgets-enterAddressStateOrRegion-dropdown-nativeId"]'))
                    #         select.select_by_visible_text(row['送付先住所都道府県'])
                            time.sleep(2)

                            address_line1 = row['送付先住所郡市区'] + row['送付先住所それ以降の住所']
                            address_line1_input = driver.find_element(By.XPATH, '//*[@id="address-ui-widgets-enterAddressLine1"]')
                            address_line1_input.clear()
                            address_line1_input.send_keys(address_line1[:16])
                            time.sleep(2)

                            address_line2_input = driver.find_element(By.XPATH, '//*[@id="address-ui-widgets-enterAddressLine2"]')
                            address_line2_input.send_keys(address_line1[16:32])
                            time.sleep(2)

                            building_name_input = driver.find_element(By.XPATH, '//*[@id="address-ui-widgets-enterBuildingOrCompanyName"]')
                            building_name_input.send_keys(address_line1[32:48])

                            unit_input = driver.find_element(By.XPATH, '//*[@id="address-ui-widgets-enterUnitOrRoomNumber"]')
                            unit_input.send_keys(address_line1[48:])

                            driver.find_element(By.XPATH, '//*[@id="address-ui-widgets-enterAddressFormContainer"]/div[4]/a/span/span').click()
                            time.sleep(2)
                            driver.find_element(By.XPATH, '//*[@id="address-ui-widgets-delivery-instructions-desktop-widget-html-container"]/div/div/div[1]/div[6]/div[1]/div/div/div/span/div[7]/label/input').click()
                            driver.find_element(By.XPATH, '//*[@id="address-ui-widgets-form-submit-button"]/span/input').click()

                            try:
                                driver.find_element(By.XPATH, '//*[@id="nav-link-accountList"]').click()
                                time.sleep(2)
                                driver.find_element(By.XPATH, '//*[@id="a-page"]/div[1]/div/div[3]/div[1]/a').click()
                                time.sleep(2)
                                driver.find_element(By.XPATH, '//*[@id="ya-myab-plus-address-icon"]').click()
                                st.text("入力完了")
                                st.text(full_name)
                            except:
                                driver.find_element(By.XPATH, '//*[@id="nav-link-accountList"]').click()
                                time.sleep(2)
                                driver.find_element(By.XPATH, '//*[@id="a-page"]/div[1]/div/div[3]/div[1]/a').click()
                                time.sleep(2)
                                driver.find_element(By.XPATH, '//*[@id="ya-myab-plus-address-icon"]').click()
                                st.text("失敗した住所データ")
                                st.text(full_name)
                            # エラーが発生した場合、次の反復に移ります。
                                continue


                            # 次の住所情報に移るための遅延（必要に応じて調整）
                            time.sleep(2)






                        st.success("住所入力が完了しました")

                st.title("住所削除")    
                start_index = st.slider("削除を開始する住所番号を選択してください", min_value=1, max_value=10, value=2)
                if start_index:
                        if st.button("削除開始"):
                            # ChromeDriverのパスを指定してSelenium WebDriverを初期化
                            driver = webdriver.Chrome(options=options)
                            index = start_index-1
                            driver.get("https://www.amazon.co.jp/ap/signin?openid.pape.max_auth_age=0&openid.return_to=https%3A%2F%2Fwww.amazon.co.jp%2F%3Fref_%3Dnav_signin&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.assoc_handle=jpflex&openid.mode=checkid_setup&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0&")
                            time.sleep(seconds)

                            email_input = driver.find_element(By.XPATH, '//*[@id="ap_email"]')
                            email_input.send_keys(email)
                            driver.find_element(By.XPATH, '//*[@id="continue"]').click()
                            time.sleep(2)
                            password_input = driver.find_element(By.XPATH, '//*[@id="ap_password"]')
                            password_input.send_keys(password)
                            driver.find_element(By.XPATH, '//*[@id="signInSubmit"]').click()
                            time.sleep(seconds)
                            try:
                                driver.get("https://www.amazon.co.jp/a/addresses")
                                st.text("Amazonサインイン成功")
                                wait = WebDriverWait(driver, 10)
                            except Exception as e:
                                st.error(f"エラーが発生しましたので、Amazonにサインインできるか試行してから再実行してください。https://www.amazon.co.jp/ap/signin?openid.pape.max_auth_age=900&openid.return_to=https%3A%2F%2Fwww.amazon.co.jp%2Fgp%2Fyourstore%2Fhome%3Fpath%3D%252Fgp%252Fyourstore%252Fhome%26useRedirectOnSuccess%3D1%26signIn%3D1%26action%3Dsign-out%26ref_%3Dnav_AccountFlyout_signout&openid.assoc_handle=jpflex&openid.mode=checkid_setup&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0: {e}")
                            time.sleep(2)
                            while True:
                                try:
                                    delete_button = driver.find_element(By.XPATH, f'//*[@id="ya-myab-address-delete-btn-{index}"]')
                                    delete_button.click()
                                    time.sleep(2)
                                    confirm_delete_button = driver.find_element(By.XPATH, f'//*[@id="deleteAddressModal-{index}-submit-btn"]/span/input')
                                    confirm_delete_button.click()
                                    time.sleep(2)
                                    driver.find_element(By.XPATH, '//*[@id="nav-link-accountList"]').click()
                                    time.sleep(2)
                                    driver.find_element(By.XPATH, '//*[@id="a-page"]/div[1]/div/div[3]/div[1]/a').click()
                                    time.sleep(2)
                                except:
                                    break
        elif page =="楽天リサーチ":
            st.title("楽天リサーチ")
            shopName = st.text_input("リサーチする楽天ショップIDを入力してください")
            options = [("売れてる順", "standard"),
                            ("価格昇順", "+itemPrice"),
                            ("価格降順", "-itemPrice")]
            label, sort = st.selectbox("並び替え", options, format_func=lambda x: x[0])
            rakuten_API = st.text_input("楽天APIキーを入力してください")
            # ラベルから対応するキーを見つける
            if shopName and rakuten_API:
                if st.button("楽天データ取得開始"):
                    counter = 0
                    url = 'https://app.rakuten.co.jp/services/api/IchibaItem/Search/20170706'

                    payload = {
                        'applicationId': rakuten_API,
                        'hits': 30,
                        'shopCode': shopName,
                        'page': 1,
                        'postageFlag': 0,
                        'sort': sort
                    }
                    r = requests.get(url, params=payload)
                    resp = r.json()
                    total = int(resp['count'])

                    Max = min((total // 30) + 1, 100)  # 最大ページ数の制限

                    columns = ["JAN", "NAME", "PRICE", "URL", "AVAILABLE", "REVIEW", "POSTAGE", "ITEM_CODE", "ITEM_CAPTION", "CATCHCOPY"]
                    df = pd.DataFrame(columns=columns)
                # 初期のページ数とヒット数の設定
                    initial_payload = {
                        'applicationId': rakuten_API,
                        'hits': 30,
                        'shopCode': shopName,
                        'page': 1,
                        'postageFlag': 0,
                        'sort': sort
                    }
                    initial_response = requests.get(url, params=initial_payload).json()
                    total_items = int(initial_response['count'])
                    max_pages = min((total_items // 30) + 1, 100)  # 最大100ページまでとする

                    progress_bar = st.progress(0)

                    for page_number in range(1, max_pages + 1):
                        payload = {
                            'applicationId': rakuten_API,
                            'hits': 30,
                            'shopCode': shopName,
                            'page': page_number,
                            'postageFlag': 0,
                            'sort': sort
                        }
                        response = requests.get(url, params=payload).json()

                        for item in response['Items']:
                            item_details = item['Item']
                            JAN = item_details['itemUrl'][-13:]
                            data = {
                                "JAN": JAN,
                                "NAME": item_details['itemName'],
                                "PRICE": item_details['itemPrice'],
                                "URL": item_details['itemUrl'],
                                "AVAILABLE": item_details['availability'],
                                "REVIEW": item_details['reviewCount'],
                                "POSTAGE": item_details['postageFlag'],
                                "ITEM_CODE": item_details["itemCode"],
                                "ITEM_CAPTION": item_details['itemCaption'],
                                "CATCHCOPY": item_details["catchcopy"]
                            }
                            new_row = pd.DataFrame([data])
                            df = pd.concat([df, new_row], ignore_index=True)
                            counter += 1
                        progress_bar.progress(int(counter  / 30))

                    st.dataframe(df)  # データフレームを表示

                    # データフレームをExcelファイルとしてダウンロード可能にする
                    towrite = io.BytesIO()
                    df.to_excel(towrite, index=False, sheet_name='Sheet1')  # Excelファイルに書き込み
                    towrite.seek(0)  # ファイルの先頭に戻る
                    st.download_button(label="ダウンロード", data=towrite, file_name=f"{shopName}_data.xlsx")
                    
                    text = st.text_input("消したい文字がある場合")
                    
                    if text:
                        df["NAME"] = df["NAME"].replace(text,"")
                    towrite = io.BytesIO()
                    df.to_excel(towrite, index=False, sheet_name='Sheet1')  # Excelファイルに書き込み
                    towrite.seek(0)  # ファイルの先頭に戻る
                    st.download_button(label="削除後データダウンロード", data=towrite, file_name=f"{shopName}_data.xlsx")
                        





            st.title("Keepa検索")
            st.text("楽天リサーチ結果をKeepaでASIN検索します")
            
            accesskey = st.text_input("Keepa APIキーを入力してください")
            
            uploaded_file_Rakuten = st.file_uploader("楽天リサーチ結果読み込み", type=['xlsx', 'csv'])
            
            if accesskey:
                api = keepa.Keepa(accesskey)
                if uploaded_file_Rakuten:
                    if uploaded_file_Rakuten.name.endswith('.xlsx'):
                        df = pd.read_excel(uploaded_file_Rakuten)
                    else:
                        df = pd.read_csv(uploaded_file_Rakuten,encoding='shift_jis')
                    st.write(df)
                    
                st.text("間隔の目安：49€プラン→30　129€プラン→10　459€プラン→2")
                st.text("読み込む商品数が少なければ間隔は少し短くしても良い")
                seconds = st.slider("Keepaリクエストの間隔(秒)", min_value=0, max_value=200, value=10)
                if seconds:
                    lens = st.slider("読み込む商品数", min_value=1, max_value=3000, value=500)
                    if lens:
                        df = df[0:lens]


                        if st.button("ASINデータ取得開始"):
                            df_result = pd.DataFrame()

                            st.text("残りトークン")
                            token_left = st.empty()
                            st.text("進捗")
                            progress_bar = st.progress(0)

                            for i in range(0,len(df)): #len(df)
                                try:
                                    
                                    text = df.reset_index()["NAME"][i]
                                    time.sleep(seconds)
                                    product_parms = {"title":str(text)
                                                    }
                                    # apiからfinderの結果を取得
                                    finder = api.product_finder(product_parms, domain="JP")
                                    df_finder = pd.DataFrame(finder)
                                    df_finder = df_finder.rename(columns={0: str(text)})
                                    df_result = pd.concat([df_result,df_finder],axis=1)
                                    # APIから残りのトークン数を表示
                                    token_left.write(api.tokens_left)
                                    progress_bar.progress(int(i*100/len(df)))
                                except Exception as e:
                                    # エラーメッセージをStreamlit上に表示
                                    st.error(f"エラーが発生しました: {e}")
                                    break  # for文から抜ける
                            progress_bar.progress(100)
                            # df_resultの1行目を別のデータフレームに格納
                            df_result1 = df_result.iloc[[0]].T.reset_index(drop=True)
                            # 列名を'ASIN1'に変更

                            df_result1.columns = ['ASIN']
                            # df_resultの列名以外のすべてのデータを1列に格納
                            df_result_stacked = df_result.iloc[1:].stack().reset_index(drop=True)
                            # 欠損値を削除
                            df_result_stacked.dropna(inplace=True)
                            # df_result3の「ASIN2」列にデータを格納
                            df_result2 = pd.DataFrame(df_result_stacked, columns=["ASIN"])
                            st.title("一致ASIN")
                            st.write(df_result1)        
                            st.title("関連ASIN")
                            st.write(df_result2)
                            
                            towrite = io.BytesIO()
                            with pd.ExcelWriter(towrite) as writer:
                                # df_result1を'一致ASIN'シートに書き込み
                                df_result1.to_excel(writer, index=False, sheet_name='一致ASIN')

                                # df_result2を'関連ASIN'シートに書き込み
                                df_result2.to_excel(writer, index=False, sheet_name='関連ASIN')
                            # ファイルポインタを先頭に戻す
                            towrite.seek(0)

                            # ダウンロードボタンを作成し、Excelファイルをダウンロード可能にする
                            st.download_button(label="ダウンロード", data=towrite, file_name="RakutenからASIN_data.xlsx", mime="application/vnd.ms-excel")
                            
                            
                            
        elif page =="ASIN解析":
            st.title("ASIN解析")
            st.text("ASINから商品情報とセラー情報を取得します")
            accesskey = st.text_input("Keepa APIキーを入力してください")            
            if accesskey:
                api = keepa.Keepa(accesskey,timeout = 30)

                # ASINファイルのアップロード
                uploaded_file_asin = st.file_uploader("ASINファイルをアップロードしてください", type=['xlsx', 'csv'])

                if uploaded_file_asin is not None:
                    # ファイルの拡張子に応じた処理
                    if uploaded_file_asin.name.endswith('.xlsx'):
                        xls = pd.ExcelFile(uploaded_file_asin)
                        sheet_names = xls.sheet_names
                        selected_sheet = st.selectbox('シート名を選択してください', sheet_names)
                        df = pd.read_excel(uploaded_file_asin, sheet_name=selected_sheet)
                    elif uploaded_file_asin.name.endswith('.csv'):
                        df = pd.read_csv(uploaded_file_asin)

                    # アップロードされたファイルの内容を表示
                    st.write(df)
                    st.text("間隔の目安：49€プラン→30　129€プラン→10　459€プラン→2")
                    seconds = st.slider("Keepaリクエストの間隔(秒)", min_value=0, max_value=200, value=10)
                    if seconds:

                        if st.button("検索開始"):
                            st.text("残りトークン")
                            token_left = st.empty()
                            token_left.write(api.tokens_left)

                            # ASIN列の値をリストとして取得
                            asins = df["ASIN"].tolist()

                            # ASINリストで商品情報をクエリ
#                             products = api.query(items=asins, domain="JP", stats=1,buybox=True)


                            # 商品情報からDataFrameを作成
                            product_data = []
                            st.text("進捗")
                            progress_bar = st.progress(0)


                            for i in range(0, len(asins), 100):
                                try:
                                    # 現在のチャンクを取得
                                    asins_chunk = asins[i:i+100]

                                    # ASINリストの現在のチャンクで商品情報をクエリ
                                    products = api.query(items=asins_chunk, domain="JP", stats=1, buybox=True)

                                    # 各商品についての情報を処理
                                    for product in products:
                                        product_info = {
                                            'title': product.get('title', ''),
                                            'asin': product.get('asin', ''),
                                            'brand': product.get('brand', ''),
                                            'manufacturer': product.get('manufacturer', ''),
                                            'rootCategory': product.get('rootCategory', ''),
                                            'buyBoxSellerId': product.get('buyBoxSellerIdHistory', [''])[1] if len(product.get('buyBoxSellerIdHistory', [])) > 1 else '',
                                            'eanList': product.get('eanList', [''])[0] if product.get('eanList') and product['eanList'] else '',
                                            'itemHeight': product.get('itemHeight', ''),
                                            'itemLength': product.get('itemLength', ''),
                                            'itemWidth': product.get('itemWidth', ''),
                                            'itemWeight': product.get('itemWeight', '')
                                        }
                                        product_data.append(product_info)
                                        token_left.write(api.tokens_left)
                                        progress_bar.progress(int(i*100/len(asins)))
                                        time.sleep(seconds)

                                except Exception as e:
                                    # エラーメッセージを表示し、ループを抜ける
                                    st.error(f"エラーが発生しました: {e}")
                                    continue

                            # 商品情報のリストからDataFrameを作成
                            df_products = pd.DataFrame(product_data)

                            # buyBoxSellerIdの処理
                            # '-1' と '-2' を空文字列に置換し、NaNを削除
                            df_products_seller = df_products["buyBoxSellerId"].replace("-1", "").replace("-2", "").dropna()

                            # 10文字より多い値を持つ行のみを保持
                            df_products_seller = df_products_seller[df_products_seller.str.len() > 10]

                            # 空白行を削除（空白のみの行も削除される）
                            df_products_seller = df_products_seller[df_products_seller.str.strip() != ""]

                            # 重複を削除
                            df_products_seller = df_products_seller.drop_duplicates()

                            # 処理したデータフレームを表示
                            st.write(df_products)
                            st.write(df_products_seller)

                            # データフレームをExcelファイルとしてダウンロード可能にする
                            towrite = io.BytesIO()




                            with pd.ExcelWriter(towrite) as writer:
                                    # df_result1を'一致ASIN'シートに書き込み
                                    df_products.to_excel(writer, index=False, sheet_name='ASIN')

                                    # df_result2を'関連ASIN'シートに書き込み
                                    df_products_seller.to_excel(writer, index=False, sheet_name='SellerID')
                            # ファイルポインタを先頭に戻す
                            towrite.seek(0)

                            # ダウンロードボタンを作成し、Excelファイルをダウンロード可能にする
                            st.download_button(label="ダウンロード", data=towrite, file_name="ASIN解析とSellerID.xlsx", mime="application/vnd.ms-excel")


                        
                        

                    
                
            
            
            
            
            
            
            
            
            
                st.title("セラー解析")
                st.text("セラーIDからセラーASINリストを取得します")

                # ファイルアップローダーを作成
                uploaded_file_seller = st.file_uploader("Seller IDファイルをアップロードしてください", type=['xlsx', 'csv'])



                # ファイルがアップロードされた場合の処理
                if uploaded_file_seller is not None:
                    # ファイルの拡張子によって処理を分岐
                    if uploaded_file_seller.name.endswith('.xlsx'):
                        # Excelファイルの場合、利用可能なシート名を取得
                        xls = pd.ExcelFile(uploaded_file_seller)
                        sheet_names = xls.sheet_names

                        # ユーザーがシート名を選択できるようにselectboxを設置
                        selected_sheet = st.selectbox('シート名を選択してください', sheet_names)

                        # 選択されたシートを読み込む
                        df = pd.read_excel(uploaded_file_seller, sheet_name=selected_sheet)

                    elif uploaded_file_seller.name.endswith('.csv'):
                        # CSVファイルの場合、直接DataFrameに読み込む
                        df = pd.read_csv(uploaded_file_seller)

                    # DataFrameを表示
                    st.write(df)
                    df_seller_id= df.iloc[:, 0]
                    seconds = st.slider("Keepaリクエストの間隔(秒)　", min_value=0, max_value=200, value=10)
                    st.text("進捗")
                    progress_bar = st.progress(0)
                    if seconds:

                        # セラー情報を格納するための空のリストを用意
                        seller_data_list = []
                        seller_info_list = []  # セラー情報を格納するリスト
                        df_asin_list = pd.DataFrame(columns=['sellerId', 'ASIN',"address"])
                        st.text("残りトークン")
                        token_left = st.empty()
                        token_left.write(api.tokens_left)

                        if st.button("セラー検索開始"):
                            for i in range(len(df_seller_id)): #range(len(df_seller_id)
                                seller_id = df_seller_id.iloc[i]  # pandas Seriesから値を取得する場合
                                try:
                                    seller_info = api.seller_query(seller_id, domain='JP', to_datetime=True, storefront=True, update=0, wait=True)

                                    # addressの最後の要素を取得し、文字列として扱う
                                    address = seller_info[seller_id].get('address', ['No address'])[-1] if seller_info[seller_id].get('address') else 'No address'
                                    address = str(address)  # 明示的に文字列に変換

                                    # セラー情報をリストに追加
                                    seller_data = {
                                        'sellerId': seller_id,
                                        'shipsFromChina': seller_info[seller_id].get('shipsFromChina', ''),
                                        'address': address,  # 変換された文字列を使用
                                        'currentRating': seller_info[seller_id].get('currentRating', ''),
                                        'currentRatingCount': seller_info[seller_id].get('currentRatingCount', '')
                                    }
                                    asin_list = seller_info[seller_id].get('asinList', [])
                                    for asin in asin_list:
                                        # 新しい行を追加
                                        df_asin_list = df_asin_list.append({'sellerId': seller_id, 'ASIN': asin,"address":address}, ignore_index=True)

                                    
                                    
                                    seller_info_list.append(seller_data)
                                    token_left.write(api.tokens_left)
                                    progress_bar.progress(int(i*100/len(df_seller_id)))
                                    time.sleep(seconds)

                                except Exception as e:
                                    st.error(f"エラーが発生しました: {e}")
                                    continue

                            # リストからセラー情報のDataFrameを作成
                            df_sellers = pd.DataFrame(seller_info_list)

                            # 結果を表示
                            st.write(df_sellers)
                            st.write(df_asin_list)
                            towrite = io.BytesIO()
                            with pd.ExcelWriter(towrite) as writer:
                                    # df_result1を'一致ASIN'シートに書き込み
                                    df_sellers.to_excel(writer, index=False, sheet_name='df_sellers')

                                    # df_result2を'関連ASIN'シートに書き込み
                                    df_asin_list.to_excel(writer, index=False, sheet_name='df_asin_list')
                            # ファイルポインタを先頭に戻す
                            towrite.seek(0)

                            # ダウンロードボタンを作成し、Excelファイルをダウンロード可能にする
                            st.download_button(label="ダウンロード", data=towrite, file_name="Sellerリサーチ.xlsx", mime="application/vnd.ms-excel")
                                

                                    
            
            
            
            











            
        

if __name__ == "__main__":
    main()
    
    



