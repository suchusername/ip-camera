docker run\
 --rm\
 --memory 1G\
 -v $(realpath ..):/ip-camera\
 --name telegram_bot\
 -t ip-camera\