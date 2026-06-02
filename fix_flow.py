with open('/home/ubuntu/v3_scorer.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 키 이름 수정
content = content.replace(
    "inst = investor.get('institution', 0)",
    "inst = investor.get('orgn', investor.get('institution', 0))"
)
content = content.replace(
    "foreign = investor.get('foreign', 0)",
    "foreign = investor.get('frgn', investor.get('foreign', 0))"
)
content = content.replace(
    "indi = investor.get('individual', 0)",
    "indi = investor.get('prsn', investor.get('individual', 0))"
)

with open('/home/ubuntu/v3_scorer.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("수정 완료!")
