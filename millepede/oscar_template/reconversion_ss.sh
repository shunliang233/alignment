g++ PedetoDB_ss.cpp -o PedetoDB_ss.out
g++ add_param.cpp -o add_param.out

./PedetoDB_ss.out < ./millepede.res >> /eos/user/t/tarai/software/run/templates/inputforalign.txt
./add_param.out < /eos/user/t/tarai/software/run/templates/inputforalign.txt > /eos/user/t/tarai/software/run/templates/inputforalign_new.txt
cp /eos/user/t/tarai/software/run/templates/inputforalign_new.txt /eos/user/t/tarai/software/run/templates/inputforalign.txt
rm /eos/user/t/tarai/software/run/templates/inputforalign_new.txt
