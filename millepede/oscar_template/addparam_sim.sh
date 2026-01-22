g++ add_param.cpp -o add_param.out

./add_param.out < /eos/user/t/tarai/software/run/sim_templates/inputforalign.txt > /eos/user/t/tarai/software/run/sim_templates/inputforalign_new.txt
cp /eos/user/t/tarai/software/run/sim_templates/inputforalign_new.txt /eos/user/t/tarai/software/run/sim_templates/inputforalign.txt
rm /eos/user/t/tarai/software/run/sim_templates/inputforalign_new.txt
