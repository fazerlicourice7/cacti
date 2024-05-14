
docker pull klee/klee:3.1


docker rm tmp_container
docker run --name tmp_container -it --ulimit='stack=-1:-1' --mount type=bind,source="$(pwd)"/,target=/app klee/klee:3.1 /bin/bash 
#