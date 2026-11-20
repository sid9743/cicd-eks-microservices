#!/usr/bin/env bash
# Writes the new image tag into each service's Helm values file and pushes the commit.
# ArgoCD watches this repo and syncs the change to the cluster.
set -euo pipefail

TAG="${1:?usage: bump-image-tag.sh <image-tag>}"

for f in helm/values/*.yaml; do
  sed -i -E "s/^(  tag: ).*/\1\"${TAG}\"/" "$f"
done

git config user.name  "jenkins-bot"
git config user.email "jenkins-bot@users.noreply.github.com"
git add helm/values/
git commit -m "release: bump image tag to ${TAG} [skip ci]" || { echo "nothing to commit"; exit 0; }
git push "https://${GIT_USER}:${GIT_TOKEN}@github.com/sid9743/cicd-eks-microservices.git" HEAD:main
