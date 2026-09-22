# Success March Survey

PABF / Success March の顧客仮説検証用アンケートです。

## 仕様
- 公開フォームは2問のみ
- 回答者には集計結果を表示しません
- 回答はSQLiteに保存
- /admin に管理画面
- 各質問の「はい / いいえ」の人数・割合・円グラフ
- 総回答数
- 10秒ごとの自動更新
- CSVエクスポート
- 同一ブラウザでの送信連打・再送信を抑制

## 管理者パスワード
管理者パスワードはリポジトリに保存しません。公開時に環境変数 `ADMIN_PASSWORD` を設定してください。

## 起動
```bash
pip install -r requirements.txt
ADMIN_PASSWORD=your-password python app.py
```

回答フォーム: http://localhost:5000  
管理画面: http://localhost:5000/admin

## 公開
Render等のPython Webサービスにそのままデプロイできるよう `render.yaml` と `Dockerfile` を含めています。
