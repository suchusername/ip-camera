docker run\
 --rm\
 -v $(realpath ..):/ip-camera\
 --name telegram_bot\
 -t ip-camera\
 python /ip-camera/bot/bot.py