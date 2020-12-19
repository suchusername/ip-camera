docker run\
 --rm\
 --memory 1500M\
 -v $(realpath ..):/ip-camera\
 --name telegram_bot\
 -t ip-camera\
