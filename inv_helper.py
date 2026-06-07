import os
def get_investor_data(code):
    p=os.path.join('kis_stock_data',str(code)+'.csv')
    if not os.path.exists(p): return {'frgn':0.0,'orgn':0.0}
    lines=[l for l in open(p).read().splitlines() if l.strip()]
    if len(lines)<2: return {'frgn':0.0,'orgn':0.0}
    f=lines[-1].split(',')
    def g(i):
        try: return float(f[i])
        except: return 0.0
    return {'frgn':g(3),'orgn':g(4)}
