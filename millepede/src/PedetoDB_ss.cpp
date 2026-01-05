//side by side 

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
    bool sidebyside=false;
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
            if(moduleId%10!=0)sidebyside=true;
            p[moduleId][paramId*5]+=value, used[moduleId]=true;
        }
         getline (cin,dump);
    }
    if(sidebyside){
        rep(i,4)rep(j,3)rep(k,8){
        moduleId=(i+1)*1000+j*100+k*10;
        if(used[moduleId]&&used[moduleId+1]){
            if((k==0)||(k==2)||(k==5)||(k==7))p[moduleId][1]=(p[moduleId+1][0]-p[moduleId][0])/(2.0*0.020);
	    else p[moduleId][1]=(p[moduleId][0]-p[moduleId+1][0])/(2.0*0.020);
            p[moduleId][0]=(p[moduleId][0]+p[moduleId+1][0])/2.0;
           // p[moduleId][5] does not have to change
        }
    }

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
        moduleId=(i+1)*1000+j*100+k*10;
        if(used[moduleId]){
            if(flag)cout<<",";
            cout<<"\""<< std::setfill('0') << std::setw(3) << ((moduleId/10)-100);
	    cout<<setw(0);
	    cout<<"\": ["<<p[moduleId][0];
            rep(id,5)cout<<", "<<p[moduleId][id+1];
            cout<<"]";
            flag=true;
        }
    }

    return 0;
}
