import re

input = "here some number AP12DB.43DE.78E8 for testing"
matches = re.findall(r'\bAP[0-9A-Fa-f]{4}\.[0-9A-Fa-f]{4}.[0-9A-Fa-f]{4}\b', input)
print(matches)


#AP1006.ED4D.32D0
