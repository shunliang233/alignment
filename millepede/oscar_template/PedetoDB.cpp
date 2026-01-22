#include<bits/stdc++.h>
using namespace std;
#define rep(i, n) for(int i = 0; i < n; ++i)
#define N 100000

int main(void){
    double p[N][6]={};
    bool used[N];
    int moduleId;
    int paramId;
    double value;
    bool flag=false;
    string dump;

    getline (cin,dump);
    while(cin>>moduleId){
        cin>>value;
        paramId=moduleId%10-1; //[1-6]
        moduleId/=10;
        if(moduleId<10){ //[1-4]
            p[moduleId][paramId]+=value, used[moduleId]=true;
        }
        else if(moduleId<100){//[2-4][0-2]
            if(paramId>=2)paramId++;
            p[moduleId][paramId]+=value, used[moduleId]=true;
        }
        else{//[2-4][0-2][0-7]
            moduleId/=10;
            p[moduleId][paramId*5]+=value, used[moduleId]=true;
        }
         getline (cin,dump);
    }
    rep(i,4){
        moduleId=(i+1);
        if(used[moduleId]){
            if(flag)cout<<",";
            cout<<"\""<< std::setfill('0') << std::setw(1)<< (moduleId-1);
	    cout<<setw(0);
	    cout <<"\": ["<<p[moduleId][0];
            rep(id,5)cout<<", "<<p[moduleId][id+1];
            cout<<"]";
            flag=true;
        }
    }

    rep(i,4)rep(j,3){
        moduleId=(i+1)*10+j;
        if(used[moduleId]){
            if(flag)cout<<",";
            cout<<"\""<< std::setfill('0') << std::setw(2)<< (moduleId-10);
	    cout<<setw(0);
	    cout<<"\": ["<<p[moduleId][0];
            rep(id,5)cout<<", "<<p[moduleId][id+1];
            cout<<"]";
            flag=true;
        }
    }

    rep(i,4)rep(j,3)rep(k,8){
        moduleId=(i+1)*100+j*10+k;
        if(used[moduleId]){
            if(flag)cout<<",";
            cout<<"\""<< std::setfill('0') << std::setw(3) << (moduleId-100);
	    cout<<setw(0);
	    cout<<"\": ["<<p[moduleId][0];
            rep(id,5)cout<<", "<<p[moduleId][id+1];
            cout<<"]";
            flag=true;
        }
    }

    return 0;
}
