//Fixfromstep1.cpp

#include<bits/stdc++.h>
using namespace std;
#define rep(i, n) for(int i = 0; i < n; ++i)
#define N 100000

int main(void){
    int paramId;
    double value;
    int SLid; //station and layer id
    string dump;

    cout<<"*            Initial parameter values, presigmas"<<endl;
    cout<<"Parameter        ! define parameter attributes (start  of list)"<<endl;

    getline (cin,dump);
    while(cin>>paramId){
        cin>>value;
        if(paramId<1000)SLid=paramId/10;
        else SLid=paramId/1000;
        if((SLid!=21)&&(SLid!=41))cout<<paramId<<" "<<value<<"  "<<"-1.  ! fix parameter at value"<<endl;
    
         getline (cin,dump);
    }
    

    return 0;
}
