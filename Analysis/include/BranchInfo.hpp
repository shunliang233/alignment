#pragma once

#include <string>
#include <iostream>

class BranchInfo {
public:
    BranchInfo(const std::string& name, const std::string& typeName, const std::string& title)
        : name_(name), typeName_(typeName), title_(title) {}
    
    const std::string& getName() const { return name_; }
    const std::string& getTypeName() const { return typeName_; }
    const std::string& getTitle() const { return title_; }
    
    friend std::ostream& operator<<(std::ostream& os, const BranchInfo& info);
    
private:
    std::string name_;
    std::string typeName_;
    std::string title_;
};

inline std::ostream& operator<<(std::ostream& os, const BranchInfo& info) {
    char buffer[100];
    std::snprintf(buffer, sizeof(buffer), "%-50s %-20s", 
                  info.name_.c_str(), info.typeName_.c_str());
    os << buffer;
    return os;
}
