from datetime import datetime
def overlap(a,b,c,d):return a<d and c<b
assert overlap(600,660,645,675) is True
assert overlap(600,660,660,690) is False
assert overlap(600,660,540,600) is False
assert (30<=30<=120) and (30<=120<=120)
assert not (30<=15<=120) and not (30<=135<=120)
print("PASS: half-open interval and duration reference examples only; not DB concurrency tests")
