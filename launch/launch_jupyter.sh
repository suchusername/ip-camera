docker run\
 -d\
 --rm\
 -v $(realpath ..):/ip-camera\
 --name jupyter_lab\
 -p 5001:5001\
 --entrypoint=""\
 -t ip-camera\
 jupyter lab\
 --ip 0.0.0.0\
 --port 5001\
 --allow-root\
 --NotebookApp.token=''\
 --NotebookApp.password=''\
