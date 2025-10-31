import ROOT
import os
import argparse
from Dataset import Dataset

# python3 draw_chi2_hist.py -y 2023 -r 011705 -f 450-500

def draw_chi2_hist_for_dir(in_dir, out_path):
    chain = ROOT.TChain("tree")
    for fname in os.listdir(in_dir):
        if fname.endswith(".root"):
            chain.Add(os.path.join(in_dir, fname))
    if chain.GetEntries() == 0:
        print(f"[Warning] No entries in {in_dir}")
        return
    h_chi2 = ROOT.TH1D("h_chi2", "fitParam_chi2/ndf;chi2/ndf;Entries", 100, 0, 10)
    chain.Draw("fitParam_chi2/fitParam_ndf>>h_chi2")
    c1 = ROOT.TCanvas("c1", "Chi2 Histogram", 800, 600)
    h_chi2.Draw()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    c1.SaveAs(out_path)
    print(f"Saved: {out_path}")
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Draw chi2/ndf hist for all iterations.")
    parser.add_argument('-y', '--year', type=str, required=True, help='Year (e.g., 2022-2025)')
    parser.add_argument('-r', '--run', type=str, required=True, help='Run number (e.g., 011705)')
    parser.add_argument('-f', '--files', type=str, required=True, help='Raw file number or range (e.g., 400-500)')
    args = parser.parse_args()

    base_dir = os.path.abspath(os.path.dirname(__file__))
    dataset = Dataset(args.year, args.run, args.files, base_dir)
    data_dir = dataset.data_dir
    draw_dir = os.path.join(base_dir, "Draw")
    
    
    # 遍历 iterXX/2kfalignment 目录
    for it in dataset.iter_dirs():
        in_dir = os.path.join(it.dir, "2kfalignment")
        out_name = f"iter{it.num:02d}_chi2_hist.png"
        out_path = os.path.join(draw_dir, dataset.name, out_name)
        # draw_chi2_hist_for_dir(in_dir, out_path)