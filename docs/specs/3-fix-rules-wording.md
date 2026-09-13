# rules/development.mdの誤解を招く文言を修正

対象Issue: #3

## 実装方針

`.claude/rules/development.md`の「mainから直接ブランチを切ったり」という表現を、「start-implementation skillを経由せず、手動でブランチ作成・実装着手をしないこと」だと明確に伝わる文言に書き換える。ブランチの親をmainにすること自体は正しい手順(`start-implementation`のスクリプトも`origin/main`からブランチを作る)であり、それを禁止しているわけではないことが分かるようにする。

## 完了条件
- [x] rules/development.mdの該当箇所が、「branchの親がmainであること」の禁止ではなく「skillを経由しない手動での着手」の禁止だと明確に読める文言になっている
