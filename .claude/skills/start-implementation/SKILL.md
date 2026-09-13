---
name: start-implementation
description: Start implementation work on a confirmed GitHub Issue in kozy0810/aituber — create a branch from main, write an intent-driven spec doc under docs/specs/, and move the issue to "In progress" on the Kanban board. Use this whenever the user wants to begin coding a specific Issue, says "着手して", "実装を始めて", "このIssueをやる", "作業ブランチを切って", or similar — always before writing any implementation code for a tracked piece of work. Do not use for exploratory design discussion where no Issue exists yet; file the Issue first with the create-issue skill.
---

# 実装着手(aituberプロジェクト)

kozy0810/aituberでは、確定したIssueに着手する際、必ずこの手順を通す。mainから直接ブランチを切って何となく実装を始めたり、仕様ドキュメントを作らずにコードを書き始めたりしない。

## いつ使うか

着手対象のIssue番号が決まっている時に使う。Issueがまだ無い場合は、先に`create-issue` skillでIssue化してから使う(このskillはIssue番号を必須の起点とする)。

## 手順

1. Issue番号を確認する(会話に無ければユーザーに聞くか、`create-issue`でのIssue化を先に提案する)
2. `gh issue view <番号> --repo kozy0810/aituber --json title,body,url` でIssueの内容(実装内容・完了条件)を取得する
3. Issueタイトルから、英語の短いkebab-caseスラッグを考える(例:「YouTube Liveのコメント取得を実装する」→ `youtube-live-chat`)
4. `scripts/start_implementation.sh --issue <番号> --slug <スラッグ>` を実行する。これが以下を行う:
   - mainを最新化(`git checkout main && git pull`)
   - `issue-<番号>-<スラッグ>` ブランチを作成
   - Kanbanボード上の該当IssueのStatusを "In progress" に更新
5. `docs/specs/<番号>-<スラッグ>.md` に仕様ドキュメントを作成する(フォーマットは下記)
6. 仕様ドキュメントの内容に沿って実装を開始する

確認は不要。ユーザーに提示して止まる必要はなく、そのまま進めてよい。

## 仕様ドキュメントのフォーマット

Issueの「実装内容」を、実際にどう実装するかの技術的判断まで具体化したものが仕様ドキュメント。Issue本文をコピーするのではなく、一段深掘りする。

```markdown
# {Issueタイトル}

対象Issue: #<番号>

## 実装方針
{何をどう実装するか。使用する技術・API、変更するファイル/モジュール、主要な設計判断}

## 完了条件
{Issueの完了条件を転記。実装を進める中でより具体的なチェック項目に分割してよい}
- [ ] ...
```

このドキュメントはPRマージ後も`docs/specs/`に残す(将来の設計判断を追える記録として蓄積する方針。2026-09-13決定)。

## 補足

- ブランチ命名は `issue-<番号>-<スラッグ>` に固定する
- マージ戦略: このリポジトリはSquash and Mergeのみ許可されるようリポジトリ設定済み。PR作成・マージ時に迷う必要はない
- 対象リポジトリ・Kanbanボードの各種IDはスクリプトに埋め込み済み。ボードを作り直した場合はスクリプト冒頭のコメントに従って取り直す
