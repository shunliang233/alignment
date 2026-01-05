#include<bits/stdc++.h>
using namespace std;
#define rep(i, n) for(int i = 0; i < n; ++i)
#define N 100000

int main(void){
    map<string,vector<double> >mp;
    vector<string>idd;
    vector<double>a,b;
    bool flag=false;
    bool id_val=false;
    string str,id,val;
    bool pre=false;

    while(getline (cin,str)){
        rep(i,str.size()){
            if((!flag)&&str[i]!='"')continue;
            if(str[i]==' ')continue;
            if(str[i]=='[')continue;
            if(str[i]==':')continue;
            if((str[i]==',')||(str[i]==']')){
                a.push_back(atof(val.c_str()));
                val="";
                if(str[i]==']'){
                    if(mp[id].empty())mp[id]=a;
                    else{
                        b=mp[id];
                        rep(j,6)b[j]+=a[j];
                        mp[id]=b;
                    }
                    id="";
                    a.clear();
                    flag=false;
                }
                continue;
            }
            if(str[i]=='"'){
              id_val=(!id_val),flag=true;
              continue;
            }
            if(id_val)id+=str[i];
            else val+=str[i];
        }
    }

    map<string,vector<double> >::iterator itr=mp.begin();
    while(itr!=mp.end()){
        if(pre)cout<<",";
        cout<<"\""<<(*itr).first<<"\": ["<<((*itr).second)[0];
        rep(j,5)cout<<", "<<((*itr).second)[j+1];
        cout<<"]";
        pre=true;
        itr++;
    }
                    


    return 0;
}