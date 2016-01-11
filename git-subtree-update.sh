#!/bin/bash
pyura_remote="ssh://git@int-wenzelvcs.int.kit.edu/projects/pyura.git"

git diff --exit-code > /dev/null
if [ $? -ne 0 ]; then
    echo "Your working tree has modifications. Commit and try again."
    exit 1
fi

git remote -v | grep pyura.git 2>&1 > /dev/null
if [ $? -ne 0 ]; then
    # switch branches to make sure we have pyura_branch
    git checkout pyura_branch > /dev/null
    git checkout master > /dev/null
    echo "Adding remote: $pyura_remote"
    git remote add pyura_remote $pyura_remote
    echo "Fetching remote..."
    git fetch pyura_remote
    echo "Setup pyura_branch to track pyura_remote"
    git branch pyura_branch --set-upstream-to pyura_remote/master 
fi

git fetch pyura_remote
git subtree merge -P WaNo/lib/pyura pyura_remote/master --squash 
