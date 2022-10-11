import time


contract.reset(wallets['test_key'], count=8)
time.sleep(7)

result = contract.get_count()
print("jenesis run output:"+str(result))

