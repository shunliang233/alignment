// Fixfromstep1.cpp

#include <iostream>
#include <string>

using std::cin;
using std::cout;
using std::endl;
using std::getline;
using std::string;

// Fix layers except for 21 and 41
int main(void)
{
    int paramId;
    double value;
    int SLid; // station and layer id
    string dump;

    cout << "*            Initial parameter values, presigmas" << endl;
    cout << "Parameter        ! define parameter attributes (start  of list)" << endl;

    getline(cin, dump);
    while (cin >> paramId)
    {
        cin >> value;
        if (paramId < 1000)
            SLid = paramId / 10;
        else
            SLid = paramId / 1000;
        if ((SLid != 10) && (SLid != 11) && (SLid != 12))
            cout << paramId << " " << value << "  " << "-1.  ! fix parameter at value" << endl;

        getline(cin, dump);
    }

    return 0;
}
