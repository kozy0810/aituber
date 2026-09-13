---
name: create-issue
description: Create a GitHub Issue for the kozy0810/aituber repository and register it on its "AI Tuber" Kanban board (kozy0810/projects/3) with Status/Priority/Size set. Use this whenever the user asks to file a task, turn a decided piece of work into a ticket, "Issue化して", "タスクを起票して", "Issueを作って", or otherwise wants confirmed work tracked on the board — not for open-ended design discussion that hasn't been decided yet.
---

# Issue作成(aituberプロジェクト)

kozy0810/aituberリポジトリでは、インテント駆動開発の実行単位としてGitHub Issueを使う。このskillは、確定した作業を「実装内容」と「完了条件」だけのIssueにして起票し、Kanbanボード(kozy0810/projects/3, "AI Tuber")に登録するところまでを担う。

## いつ使うか

会話の中で「これを実装しよう」「タスクにしておいて」のように、**やることが確定した**タイミングで使う。まだ方針が固まっていない検討段階の話(仕様の議論、設計の選択肢比較)をIssue化しないこと。検討中の内容は`tmp/`や`docs/`のドキュメントに置く場所であり、Issueの置き場所ではない。

## Issue本文のフォーマット

本文は次の2セクションのみ。他のセクション(背景、Out of Scope、関連リンクなど)は付け加えない。これは意図的な決定であり、Issueを軽量に保つため。

```markdown
## 実装内容
{何を実装・変更するか。誰が読んでも着手できる具体性で書く}

## 完了条件
- [ ] {客観的に確認できる完了条件}
- [ ] {客観的に確認できる完了条件}
```

- 「実装内容」は手順書ではなく、何を作る/変えるかの説明。手段の詳細まで固定しすぎない(実装者の裁量を残す)
- 「完了条件」はチェックボックスで、Yes/Noで判定できる粒度にする。「良い感じに動く」のような曖昧な条件は避ける

## Priority / Size の決め方

このプロジェクトのKanbanボードには `Priority`(P0/P1/P2)と `Size`(XS/S/M/L/XL)というSingle Selectフィールドがある。Issue作成時に両方とも値を設定する。

- Priority: P0=これが無いと配信システムとして成立しない/他の作業をブロックする、P1=通常の優先度、P2=後回しにしても支障がない
- Size: 作業ボリュームの目安。XS=1時間未満の軽微な変更、S=半日程度、M=1〜2日、L=それ以上のまとまった機能、XL=複数のサブタスクに分けた方がよい規模(その場合は先に分割を提案する)

会話の文脈から自分で妥当な値を判断する。判断がつかない場合のみ聞く。

## ラベル

現時点ではラベルを使わない。Status/Priority/Sizeのフィールドで管理する方針(2026-09-13時点の決定)。

## 作成手順

1. 会話から「実装内容」と「完了条件」を上記フォーマットで書き起こす
2. Priority / Size を判断する
3. 本文を一時ファイルに書き出し、`scripts/create_issue.sh` を実行する(確認は不要。作成前にユーザーへの提示は挟まない)

```bash
scripts/create_issue.sh \
  --title "<Issueタイトル>" \
  --body-file <本文を書いた一時ファイルのパス> \
  --priority P0|P1|P2 \
  --size XS|S|M|L|XL
```

スクリプトが以下を自動で行う。

- `kozy0810/aituber` にIssueを作成
- 作成したIssueをプロジェクトボード(kozy0810/projects/3)に追加
- Status を "Backlog"、Priority と Size を指定値に設定

成功すると作成されたIssueのURLが標準出力に出る。これをユーザーに報告する。

## 例

**Input:** 「YouTube Liveのコメント取得を`liveChatMessages.streamList`で実装するタスクを起票して」

**Output:**

タイトル: `liveChatMessages.streamListによるコメント取得の実装`

```markdown
## 実装内容
YouTube Live Streaming APIの`liveChatMessages.streamList`を使い、配信中のライブチャットメッセージ(通常コメント・スーパーチャットの`superChatEvent`を含む)を継続的に取得する処理を実装する。固定間隔のポーリングではなく、APIから返る`pollingIntervalMillis`に従う。

## 完了条件
- [ ] `liveChatMessages.streamList`でライブチャットを取得できる
- [ ] `superChatEvent`を識別し、金額を取得できる
- [ ] レート制限エラー時にAPIの推奨間隔まで待機してリトライする
```

Priority: P1 / Size: M と判断 → `scripts/create_issue.sh` 実行 → Issue URLを報告。

## 補足

- 対象リポジトリ・ボードはこのプロジェクト専用に固定してある(スクリプト内のIDを参照)。ボードを作り直した場合はスクリプト冒頭のコメントに従ってIDを取り直す
- 大きすぎる作業(Size=XL相当)は、先にサブタスクへの分割を提案してから、それぞれをIssue化する
