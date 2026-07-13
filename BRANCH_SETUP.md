# Creating or refreshing the evidence branch

This directory is prepared as the root of a separate `evidence` branch, not as a
folder to merge into `main`.

A safe Git workflow is:

```bash
git switch --orphan evidence
git rm -rf .
# copy this seed directory into the repository root
git add .
git commit -m "Seed version-matched Nocturne evidence"
git push -u origin evidence
```

Create the branch from a clean working tree. Keep the prior repository or a
local archive until both branches are visible remotely.
