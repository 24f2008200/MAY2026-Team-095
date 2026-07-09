The repo returned a 404 — it may be **private**, which means I can't access it directly. No problem — I have everything I need to customize the guide for your team.

---

## Collaborative Git Development — Team Sputnik (MAY2026-Team-095)

---

## Phase 1 — One-Time Setup (Each Member Does This)

### Step 1 — Install Git
```bash
# Check if already installed
git --version

# If not, install
sudo apt install git        # Ubuntu/Linux
# or download from git-scm.com for Windows/Mac
```

### Step 2 — Configure Your Identity
```bash
# pbn
git config --global user.name "pbn"
git config --global user.email "pbn@student.iitm.ac.in"

# annapoorani
git config --global user.name "annapoorani"
git config --global user.email "annapoorani@student.iitm.ac.in"

# roshan
git config --global user.name "roshan"
git config --global user.email "roshan@student.iitm.ac.in"

# jishan
git config --global user.name "jishan"
git config --global user.email "jishan@student.iitm.ac.in"

# rahul
git config --global user.name "rahul"
git config --global user.email "rahul@student.iitm.ac.in"
```
> Each member runs **their own block** only. This tags every commit with your name.

### Step 3 — Clone the Repository
```bash
git clone https://github.com/24f2008200/MAY2026-Team-095.git
cd MAY2026-Team-095
```
> All 5 members clone this same URL.

---

## Phase 2 — Branching Strategy

**Nobody works directly on `main`. Ever.**

```
main                        ← stable, working code only
  └── dev                   ← integration branch (merge here first)
        ├── feature/pbn-api-endpoints
        ├── feature/annapoorani-complaint-form
        ├── feature/roshan-dashboard-ui
        ├── feature/jishan-resident-login
        └── feature/rahul-manager-pages
```

### Creating Your Branch
```bash
# Always branch from dev, not main
git checkout dev
git pull origin dev

# Each member creates their own branch
# pbn
git checkout -b feature/pbn-api-endpoints

# annapoorani
git checkout -b feature/annapoorani-complaint-form

# roshan
git checkout -b feature/roshan-dashboard-ui

# jishan
git checkout -b feature/jishan-resident-login

# rahul
git checkout -b feature/rahul-manager-pages
```

**Naming convention for MAY2026-Team-095:**
| Type | Example |
|------|---------|
| New feature | `feature/pbn-swagger-docs` |
| Bug fix | `fix/roshan-navbar-bug` |
| Documentation | `docs/annapoorani-readme` |
| Testing | `test/jishan-api-endpoints` |

---

## Phase 3 — Daily Development Workflow

### Every morning before coding:
```bash
git checkout dev
git pull origin dev                    # sync with teammates' latest

git checkout feature/your-branch
git merge dev                          # bring updates into your branch
```

### As you code — commit often:
```bash
# Step 1 — see what changed
git status

# Step 2 — stage changes
git add filename.js       # specific file
git add .                 # all changed files

# Step 3 — commit with a meaningful message tied to your Jira ticket
git commit -m "feat: KAN-27 implement and integrate the API"
```

### Commit message convention for Team Sputnik:
```
feat:     KAN-XX  new feature
fix:      KAN-XX  bug fix
docs:     KAN-XX  documentation
test:     KAN-XX  adding tests
refactor: KAN-XX  code restructure
```
> Including the KAN ticket number links your commit directly to your Jira card.

---

## Phase 4 — Pushing Your Work

```bash
# First push of a new branch
git push -u origin feature/your-branch

# Subsequent pushes
git push origin feature/your-branch
```

---

## Phase 5 — Pull Request and Review

1. Go to **https://github.com/24f2008200/MAY2026-Team-095**
2. Click **"Compare & pull request"**
3. Set:
```
base:     dev
compare:  feature/your-branch
```
4. Title format: `[KAN-XX] Brief description`
5. Assign a **reviewer** from the team

### Suggested review pairs for Team Sputnik:
| Author | Reviewer |
|--------|----------|
| pbn | annapoorani |
| annapoorani | roshan |
| roshan | jishan |
| jishan | rahul |
| rahul | pbn |

6. Reviewer approves or requests changes
7. After approval → click **"Merge Pull Request"**
8. Delete the feature branch after merging

---

## Phase 6 — Handling Merge Conflicts

```bash
# Git flags the conflict inside the file like this:
<<<<<<< HEAD (your changes)
const title = "Complaint Form";
=======
const title = "Submit Complaint";
>>>>>>> dev (teammate's changes)
```

**To resolve:**
1. Open the file and decide which version to keep
2. Remove the `<<<<`, `====`, `>>>>` markers
3. Then:
```bash
git add filename.js
git commit -m "fix: resolve merge conflict in complaint form"
git push origin feature/your-branch
```

---

## Daily Cheat Sheet — MAY2026-Team-095

```bash
# Morning — sync up
git checkout dev
git pull origin dev
git checkout feature/your-branch
git merge dev

# During work
git add .
git commit -m "feat: KAN-XX describe what you did"

# End of day
git push origin feature/your-branch

# When feature complete → raise PR on GitHub
# Wait for teammate review → merge → delete branch
```

---

## Team Rules — Team Sputnik

| Rule | Owner |
|------|-------|
| No direct push to `main` | All members |
| Every PR needs approval from assigned reviewer | Reviewer pair above |
| Pull from `dev` every morning | All members |
| Commit messages must include KAN ticket number | All members |
| Delete branch after merging | Author |
| One Jira ticket = one branch | All members |

---

> **Note on private repo:** If the repo is private and new members can't clone it, **pbn** (as the repo owner under `24f2008200`) needs to go to:
> `GitHub → Settings → Collaborators → Add people`
> and invite each member by their GitHub username.
