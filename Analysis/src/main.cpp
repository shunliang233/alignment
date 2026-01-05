#include <iostream>
#include <string>
#include <vector>
#include <argparse/argparse.hpp>

#include "Analyser.hpp"

int main(int argc, char *argv[])
{
    argparse::ArgumentParser program("analysis", "1.0.0");
    program.add_argument("file")
        .help("Input ROOT file path");
    program.add_argument("-t", "--tree")
        .default_value(std::string("tree"))
        .help("Name of TTree");
    program.add_argument("-n", "--entries")
        .default_value(-1)
        .scan<'i', int>()
        .help("Number of entries to display");
    program.add_argument("-o", "--output")
        .default_value(std::string("vector_lengths.pdf"))
        .help("Output PDF file");
    try
    {
        program.parse_args(argc, argv);
    }
    catch (const std::exception &err)
    {
        std::cerr << err.what() << std::endl;
        std::cerr << program;
        return 1;
    }
    std::string file = program.get<std::string>("file");
    std::string treeName = program.get<std::string>("--tree");
    int numEntries = program.get<int>("--entries");
    std::string outputPdf = program.get<std::string>("--output");

    try
    {
        Analyser analyser(file, treeName);

        analyser.printSummary();

        // std::cout << "\nAnalyzing vector branches..." << std::endl;
        // analyser.createVectorLengthHistograms(outputPdf);
    }
    catch (const std::exception &e)
    {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }

    return 0;
}
