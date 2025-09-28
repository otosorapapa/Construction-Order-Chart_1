# 工事受注案件の予定表（ガントチャート）

Streamlit + Plotly で構築した工事案件の予定表アプリです。紙帳票のガントチャートを Web 化し、フィルタリング・検索・CSV/JSON 入出力・クリック編集・PNG 出力などの機能を備えています。

## セットアップ

Python 3.11 以降で動作確認しています。

```bash
# 仮想環境の作成 (macOS/Linux)
python -m venv venv
source venv/bin/activate

# Windows (PowerShell)
python -m venv venv
venv\\Scripts\\Activate.ps1

# 依存関係のインストール
pip install -r requirements.txt

# PNG 出力が必要な場合は追加で Kaleido をインストール
pip install kaleido

# アプリの起動
streamlit run app.py
```

## 使い方

1. 画面左のサイドバーで表示期間、検索ワード、工種・進捗・担当者で絞り込みができます。
2. 「CSV/JSON インポート」でローカルファイルから案件を取り込みます。列名が異なる場合はカラムマッピングを行ってください。
3. 案件一覧テーブルのチェックボックスで選択した案件は、ガントチャート上で強調表示されます。テーブルではキーボード操作 (↑↓ 移動、Enter で編集、Ctrl+Z/Ctrl+Y で Undo/Redo) も利用できます。
4. ガントチャートのバーをクリックすると右側に編集フォームが表示され、区間名・日付・進捗・メモを更新できます。ドラッグでの直接リサイズは Streamlit の制約により非対応ですが、クリック→日付入力で操作できます。
5. 「CSVエクスポート」「JSONエクスポート」で現在の案件データをダウンロードできます。
6. 「PNG生成」→「PNGダウンロード」で表示中のガントチャートを画像として保存できます。PDF として出力する場合は PNG を開いてブラウザ印刷を行い、A3 横向き・余白小に設定するときれいに出力できます。

## データ仕様

- projects: `name, client, site, work_type (建築/土木/その他), owner, progress (予定/進行/完了), start_date, end_date` が必須です。
- 複数区間が必要な場合はアプリ内で編集・追加できます。セグメントは `project_id, label, start_date, end_date` を持ちます。
- CSV/JSON インポート時はすべての必須カラムをマッピングしてください。

## 既知の制約

- ガントバーのドラッグ操作による伸縮は Streamlit の仕様により未対応です。クリックして日付入力で調整してください。
- 画像出力は PNG のみです。PDF は PNG をブラウザ印刷することで代替できます。

## テスト

ユニットテストは以下で実行できます。

```bash
pytest
```
