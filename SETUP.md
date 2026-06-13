# セットアップ手順

## 1. Gemini APIキー取得（無料）
1. https://aistudio.google.com にGoogleアカウントでログイン
2. 左メニュー「Get API key」→「Create API key」
3. 表示されたキーをコピーして保存

## 2. Tavily APIキー取得（無料）
1. https://app.tavily.com にメールアドレスで無料登録
2. ログイン後、APIキーが表示されるのでコピーして保存

## 3. GitHubリポジトリ作成
1. https://github.com/new でリポジトリ作成
   - Repository name: `persona-research`
   - Public にする
2. このフォルダの中身をプッシュ

```bash
cd persona-research
git init
git add .
git commit -m "initial commit"
git branch -M main
git remote add origin https://github.com/あなたのユーザー名/persona-research.git
git push -u origin main
```

## 4. GitHub Pages を有効化
1. リポジトリの Settings → Pages
2. Source: `Deploy from a branch`
3. Branch: `main` / `/ (root)`
4. Save

## 5. GitHub Secrets を登録
1. リポジトリの Settings → Secrets and variables → Actions
2. 「New repository secret」で以下を追加：
   - `GEMINI_API_KEY` ← Gemini APIキー
   - `TAVILY_API_KEY` ← Tavily APIキー

## 6. GitHub PAT（Personal Access Token）取得
1. GitHub右上アイコン → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. 「Generate new token」
3. 権限: `workflow` にチェック
4. 生成されたトークンをコピー

## 7. index.html を編集
`index.html` の上部3行を書き換える：

```javascript
const GITHUB_OWNER = "titahashi244-star";   // ← あなたのGitHubユーザー名
const GITHUB_REPO  = "persona-research";
const GITHUB_PAT   = "ghp_xxxxxxxxxxxx";    // ← 取得したPAT
```

## 8. 変更をプッシュ
```bash
git add .
git commit -m "add config"
git push
```

## 完成！
`https://titahashi244-star.github.io/persona-research/` にアクセスして使えます。
