// side by side

#include <bits/stdc++.h>
using namespace std;
#define rep(i, n) for (int i = 0; i < n; ++i)
#define N 100000

int main(void)
{
    double p[N][6] = {};
    bool used[N];
    int moduleId;
    int paramId;
    double value;
    bool flag = false;
    bool sidebyside = false;
    string dump;

    // Read millepede.res
    getline(cin, dump);
    while (cin >> moduleId)
    {
        // paramID == 0, x
        // paramID == 1, y
        // paramID == 2, z
        // paramID == 3, rx
        // paramID == 4, ry
        // paramID == 5, rz
        cin >> value;
        paramId = moduleId % 10 - 1; //[0-4]
        moduleId /= 10;
        if (moduleId < 10) //[1-4] Station
        {
            p[moduleId][paramId] += value, used[moduleId] = true;
        }
        else if (moduleId < 100) //[1-4][0-2] Layer
        {
            if (paramId >= 2) // dumpz_layers = false
                paramId++;
            p[moduleId][paramId] += value, used[moduleId] = true;
        }
        else //[1-4][0-2][0-7] Module
        {
            if (moduleId % 10 != 0)
                sidebyside = true;
            p[moduleId][paramId * 5] += value, used[moduleId] = true;
        }
        getline(cin, dump);
    }

    // The new p[moduleId] looks like alignment parameters for simulated pixel detector by two strips
    // Not really as I calucated. I don't know what's this.
    if (sidebyside)
    {
        rep(i, 4) rep(j, 3) rep(k, 8)
        {
            moduleId = (i + 1) * 1000 + j * 100 + k * 10;
            if (used[moduleId] && used[moduleId + 1])
            {
                if ((k == 0) || (k == 2) || (k == 5) || (k == 7))
                    p[moduleId][1] = (p[moduleId + 1][0] - p[moduleId][0]) / (2.0 * 0.020);
                else
                    p[moduleId][1] = (p[moduleId][0] - p[moduleId + 1][0]) / (2.0 * 0.020);
                p[moduleId][0] = (p[moduleId][0] + p[moduleId + 1][0]) / 2.0;
                // p[moduleId][5] does not have to change
            }
        }
    }

    // Stations
    rep(i, 4)
    {
        moduleId = (i + 1);
        if (used[moduleId])
        {
            if (flag)
                cout << ",";
            cout << "\"" << std::setfill('0') << std::setw(1) << (moduleId - 1);
            cout << setw(0);
            cout << "\": [" << p[moduleId][0];
            rep(id, 5) cout << ", " << p[moduleId][id + 1];
            cout << "]";
            flag = true;
        }
    }
    // Layers
    rep(i, 4) rep(j, 3)
    {
        moduleId = (i + 1) * 10 + j;
        if (used[moduleId])
        {
            if (flag)
                cout << ",";
            cout << "\"" << std::setfill('0') << std::setw(2) << (moduleId - 10);
            cout << setw(0);
            cout << "\": [" << p[moduleId][0];
            rep(id, 5) cout << ", " << p[moduleId][id + 1];
            cout << "]";
            flag = true;
        }
    }

    // Modules
    rep(i, 4) rep(j, 3) rep(k, 8)
    {
        moduleId = (i + 1) * 1000 + j * 100 + k * 10;
        if (used[moduleId])
        {
            if (flag)
                cout << ",";
            cout << "\"" << std::setfill('0') << std::setw(3) << ((moduleId / 10) - 100);
            cout << setw(0);
            cout << "\": [" << p[moduleId][0];
            rep(id, 5) cout << ", " << p[moduleId][id + 1];
            cout << "]";
            flag = true;
        }
    }

    return 0;
}
