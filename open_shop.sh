#!/bin/bash
cd ~/tollbooth
nohup python3 cashier.py > shop.log 2>&1 &
echo "Shopkeeper running (watch with: tail -f ~/tollbooth/shop.log)"
ngrok http 8000 --domain=oncoming-headband-unsoiled.ngrok-free.dev
