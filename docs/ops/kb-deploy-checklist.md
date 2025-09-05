# Knowledge Base Deployment Checklist

This checklist ensures a new Continuum Knowledge Base (KB) repo is properly deployed via **GitHub Pages (MkDocs Material + Actions).**

---

## 1. Local Setup
- [ ] `unzip continuum-knowledge-base-<version>.zip`
- [ ] `cd continuum-knowledge-base-<version>`
- [ ] `git init && git add .`
- [ ] `git commit -m "init: continuum-knowledge-base"`
- [ ] `git branch -M main`
- [ ] `git remote add origin git@github.com:<ORG_OR_USER>/continuum-knowledge-base.git`
- [ ] `git push -u origin main`

---

## 2. GitHub Repo Setup
- [ ] Repo Settings → **Pages**
  - Source → **GitHub Actions**
- [ ] Repo Settings → **Actions → General**
  - **Allow all actions and reusable workflows**
  - **Read and write permissions** for GITHUB_TOKEN
  - Leave “Allow Actions to create and approve PRs” unchecked

---

## 3. Trigger Deploy
- [ ] Push a trivial commit to `main` to trigger the Pages workflow:
  ```bash
  echo "" >> docs/index.md
  git add docs/index.md
  git commit -m "chore: trigger pages deploy"
  git push
