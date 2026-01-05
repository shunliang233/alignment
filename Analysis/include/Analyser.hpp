#pragma once

#include <string>
#include <map>
#include <vector>
#include <memory>
#include <optional>
#include <array>

#include <TFile.h>
#include <TTree.h>
#include <TBranch.h>
#include <TObjArray.h>
#include <TCanvas.h>
#include <TH1I.h>

#include "BranchInfo.hpp"

class Analyser {
public:
    Analyser(const std::string& filePath, const std::string& treeName = "tree");
    ~Analyser();
    
    // Prevent copying
    Analyser(const Analyser&) = delete;
    Analyser& operator=(const Analyser&) = delete;
    
    // Accessors
    Long64_t getEntries() const;
    
    // Analysis methods
    void printSummary();
    
private:
    void close();
    
    std::string filePath_;
    std::string treeName_;
    TFile* file_ = nullptr;
    TTree* tree_ = nullptr;
    
    static constexpr std::array<std::pair<char, const char*>, 11> TYPE_MAP = {{
        {'D', "Double_t"}, {'F', "Float_t"}, {'I', "Int_t"}, {'i', "UInt_t"},
        {'L', "Long64_t"}, {'l', "ULong64_t"}, {'S', "Short_t"}, {'s', "UShort_t"},
        {'B', "Char_t"}, {'b', "UChar_t"}, {'O', "Bool_t"}
    }};
    
    // Helper function to get type name
    static std::string getTypeName(char typeChar) {
        for (const auto& [key, value] : TYPE_MAP) {
            if (key == typeChar) return value;
        }
        return std::string(1, typeChar);
    }
};
