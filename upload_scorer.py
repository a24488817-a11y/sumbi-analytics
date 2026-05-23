import urllib.request, json, base64

token = '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'
repo = 'a24488817-a11y/sumbi-analytics'
url = f'https://api.github.com/repos/{repo}/contents/v3_scorer.py'

req = urllib.request.Request(url, headers={'Authorization': f'token {token}', 'User-Agent': 'sumbi'})
res = json.loads(urllib.request.urlopen(req).read())
sha = res['sha']
print('SHA:', sha)
