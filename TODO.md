# SnapClass AI — GitHub push fix checklist

## Completed
- Identified correct project root: `C:\Working Project's\snapclass_final yash`
- Determined Git repo is already initialized on `main`
- Found large pack history (`size-pack ~601 MiB`), likely causing RPC disconnects
- Large-file scan showed large files under `venv/` only (should be ignored)
- Confirmed remote is set to `https://github.com/yashpriraj2008-collab/Snapclass_AI.git`

## To do
- [ ] Create a safe backup of the project folder
- [ ] Create/overwrite root `.gitignore` with the provided safe rules
- [ ] Remove broken git history ONLY in the correct root (`.git`)
- [ ] Reinitialize Git cleanly (`git init`, rename branch to `main`)
- [ ] Preview staging (`git add -n .`)
- [ ] Commit clean initial snapshot
- [ ] Push to GitHub (`git push -u origin main --force`)
- [ ] Verify (`git status`, `git count-objects -vH`, `git remote -v`)

