import json

with open('config/arm.json') as f:
    arms = json.load(f)
with open('config/body.json') as f:
    bodies = json.load(f)
with open('config/hand.json') as f:
    hands = json.load(f)
with open('config/head.json') as f:
    heads = json.load(f)
with open('config/leg.json') as f:
    legs = json.load(f)
with open('config/backpack.json') as f:
    backpacks = json.load(f)
with open('config/base.json') as f:
    bases = json.load(f)
with open('config/designer.json') as f:
    designers = json.load(f)