#include <iostream>
#include <stdexcept>
#include <algorithm>
#include <cmath>

#include <TClass.h>
#include <TROOT.h>
#include <TStyle.h>
#include <TText.h>
#include <TPaveText.h>
#include <TLeaf.h>

#include "Analyser.hpp"

/**
 * @brief 构造函数：打开 ROOT 文件并获取指定的 TTree
 * @param filePath ROOT 文件路径
 * @param treeName TTree 名称（默认为 "tree"）
 * @throws std::runtime_error 如果文件无法打开或 TTree 不存在
 */
Analyser::Analyser(const std::string& filePath, const std::string& treeName)
    : filePath_(filePath), treeName_(treeName), file_(nullptr), tree_(nullptr) {
    
    file_ = TFile::Open(filePath.c_str());
    if (!file_ || file_->IsZombie()) {
        close();
        throw std::runtime_error("Cannot open ROOT file: " + filePath);
    }
    
    tree_ = dynamic_cast<TTree*>(file_->Get(treeName.c_str()));
    if (!tree_) {
        close();
        throw std::runtime_error("TTree '" + treeName + "' not found in " + filePath);
    }
}

/**
 * @brief 析构函数：清理资源
 */
Analyser::~Analyser() {
    close();
}

/**
 * @brief 关闭文件并清理指针，析构会自动关闭 TFile 和清理 TTree
 * @note 删除 TFile 会自动清理其管理的 TTree
 */
void Analyser::close() {
    delete file_;
    // 防御性：delete 后立即将指针设为 nullptr
    file_ = nullptr;
    tree_ = nullptr;
}


/**
 * @brief 获取 TTree 中的条目数
 * @return 条目总数
 */
Long64_t Analyser::getEntries() const {
    return tree_->GetEntries();
}


/**
 * @brief 打印 TTree 的摘要信息
 * @note 输出文件路径、TTree 名称、条目数和所有分支的详细信息
 */
void Analyser::printSummary() {
    std::cout << "File: " << filePath_ << std::endl;
    std::cout << "Tree: " << treeName_ << std::endl;
    std::cout << "Entries: " << getEntries() << std::endl;
    
    // 直接获取分支列表
    TObjArray* branchList = tree_->GetListOfBranches();
    std::cout << "Branches: " << branchList->GetEntries() << std::endl;
    std::cout << "\nBranch Information:" << std::endl;
    std::cout << std::string(80, '-') << std::endl;
    
    char header[100];
    std::snprintf(header, sizeof(header), "%-50s %-20s", "Name", "Type");
    std::cout << header << std::endl;
    std::cout << std::string(80, '-') << std::endl;
    
    // 遍历所有分支并打印信息
    for (Int_t i = 0; i < branchList->GetEntries(); ++i) {
        TBranch* branch = dynamic_cast<TBranch*>(branchList->At(i));
        if (branch) {
            std::string branchName = branch->GetName();
            std::string branchType = branch->GetClassName();
            // 如果分支类型为空（说明不是对象类型，而是基本数据类型）
            if (branchType.empty()) {
                // 通过分支名称获取叶子节点（Leaf）
                // Leaf 存储了基本数据类型的信息
                TLeaf* leaf = branch->GetLeaf(branchName.c_str());
                if (leaf) {
                    // 从 Leaf 获取类型名称（如 Int_t, Double_t, Float_t 等）
                    branchType = leaf->GetTypeName();
                }
            }
            
            char line[100];
            std::snprintf(line, sizeof(line), "%-50s %-20s", 
                         branchName.c_str(), branchType.c_str());
            std::cout << line << std::endl;
        }
    }
}
