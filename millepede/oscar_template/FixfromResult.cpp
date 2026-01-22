#include<bits/stdc++.h>
using namespace std;
int idx(int x){
if(x<=0)return x;
while(x>=10)x/=10;
return x;
}
int main(void){
    int moduleId;
    double value;
    string dump;
    cout<<"*            Initial parameter values, presigmas"<<endl;
    cout<<"Parameter        ! define parameter attributes (start  of list)"<<endl;
    getline (cin,dump);
    while(cin>>moduleId){
        cin>>value;
       if(idx(moduleId)>1) cout<<moduleId<<" 0.0  -1.  ! fix parameter at value"<<endl;
         getline (cin,dump);
    }
    cout<<"end ! optional for end-of-data"<<endl;
    return 0;
}

