#include<bits/stdc++.h>
using namespace std;
#define rep(i, n) for(int i = 0; i < n; ++i)
#define N 1000

int main(void){
    double p[N][8]={};
    double q[N]={}; 
    bool used[N][2]={};
    int moduleId;
    int modId;
    double value;
    bool flag=false;
    string dump;

    getline (cin,dump);
while(cin>>moduleId){
        cin>>value;
//cout<<moduleId<<" "<<value<<endl;
        if(moduleId<100){
            q[moduleId]=value;
            used[moduleId][1]=true;
        }
        else{
            modId=(moduleId/10)%10; //[0-7]
            moduleId=(moduleId/100)*10+(moduleId%10);
            p[moduleId][modId]=value;
            used[moduleId][0]=true;

        }
         getline (cin,dump);
    }
    rep(i,6){
        moduleId=10+i+1;
        if(used[moduleId][0]){
            cout<<"\""<<(moduleId/10)<<"x"<<(moduleId%10)<<"\": ["<<p[moduleId][0];
            rep(id,7)cout<<", "<<p[moduleId][id+1];
            cout<<"]";
            cout<<endl;
        }
    }
    rep(i,6){
        moduleId=10+i+1;
        if(used[moduleId][1])cout<<"\""<<moduleId<<"\": "<<q[moduleId]<<endl;
    }

    return 0;
}
