#!/bin/bash
cd /home/ubuntu
git add -A
git commit -m "auto: $(date '+%Y-%m-%d %H:%M')"
git push origin main
