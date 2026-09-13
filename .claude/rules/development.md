# 開発着手ルール

このリポジトリで実装作業に着手する時(Issueに取り掛かる、作業ブランチを作る、実装を始める、といった局面)は、必ず`start-implementation` skill(`.claude/skills/start-implementation/`)に従うこと。

mainから直接ブランチを切ったり、`docs/specs/`に仕様ドキュメントを作らずに実装を始めたりしない。

## mainへの直接pushは禁止

`main`への変更は、必ず作業ブランチ→PR→Squash and Mergeを経由すること。`git push origin <branch>:main`や、mainブランチへの直接コミット・pushは行わない。

例外は2026-09-13の`create-issue`/`start-implementation` skill自体の導入コミットのみ(ワークフローを強制する仕組みそのものがまだ存在しなかったための一度限りの措置)。それ以降はこのルールに例外を設けない。
