//side by side

#include <fstream>
#include <iostream>
#include <vector>
#include<string>

using namespace std;

class Mille 
{
 public:
  Mille(const char *outFileName, bool asBinary = true, bool writeZero = false);
  ~Mille();

  void mille(int NLC, const float *derLc, int NGL, const float *derGl,
	     const int *label, float rMeas, float sigma);
  void special(int nSpecial, const float *floatings, const int *integers);
  void kill();
  void end();

 private:
  void newSet();
  bool checkBufferSize(int nLocal, int nGlobal);

  std::ofstream myOutFile; ///< C-binary for output
  bool myAsBinary;         ///< if false output as text
  bool myWriteZero;        ///< if true also write out derivatives/labels ==0
  /// buffer size for ints and floats
  enum {myBufferSize = 5000};  ///< buffer size for ints and floats
  int   myBufferInt[myBufferSize];   ///< to collect labels etc.
  float myBufferFloat[myBufferSize]; ///< to collect derivatives etc.
  int   myBufferPos; ///< position in buffer
  bool  myHasSpecial; ///< if true, special(..) already called for this record
  /// largest label allowed: 2^31 - 1
  enum {myMaxLabel = (0xFFFFFFFF - (1 << 31))};
};

Mille::Mille(const char *outFileName, bool asBinary, bool writeZero) : 
  myOutFile(outFileName, (asBinary ? (std::ios::binary | std::ios::out) : std::ios::out)),
  myAsBinary(asBinary), myWriteZero(writeZero), myBufferPos(-1), myHasSpecial(false)
{
  // Instead myBufferPos(-1), myHasSpecial(false) and the following two lines
  // we could call newSet() and kill()...
  myBufferInt[0]   = 0;
  myBufferFloat[0] = 0.;

  if (!myOutFile.is_open()) {
    std::cerr << "Mille::Mille: Could not open " << outFileName 
	      << " as output file." << std::endl;
  }
}

//___________________________________________________________________________
/// Closes file.
Mille::~Mille()
{
  myOutFile.close();
}

//___________________________________________________________________________
/// Add measurement to buffer.
/**
 * \param[in]    NLC    number of local derivatives
 * \param[in]    derLc  local derivatives
 * \param[in]    NGL    number of global derivatives
 * \param[in]    derGl  global derivatives
 * \param[in]    label  global labels
 * \param[in]    rMeas  measurement (residuum)
 * \param[in]    sigma  error
 */
void Mille::mille(int NLC, const float *derLc,
		  int NGL, const float *derGl, const int *label,
		  float rMeas, float sigma)
{
  if (sigma <= 0.) return;
  if (myBufferPos == -1) this->newSet(); // start, e.g. new track
  if (!this->checkBufferSize(NLC, NGL)) return;

  // first store measurement
  ++myBufferPos;
  myBufferFloat[myBufferPos] = rMeas;
  myBufferInt  [myBufferPos] = 0;

  // store local derivatives and local 'lables' 1,...,NLC
  for (int i = 0; i < NLC; ++i) {
    if (derLc[i] || myWriteZero) { // by default store only non-zero derivatives
      ++myBufferPos;
      myBufferFloat[myBufferPos] = derLc[i]; // local derivatives
      myBufferInt  [myBufferPos] = i+1;      // index of local parameter
    }
  }

  // store uncertainty of measurement in between locals and globals
  ++myBufferPos;
  myBufferFloat[myBufferPos] = sigma;
  myBufferInt  [myBufferPos] = 0;

  // store global derivatives and their labels
  for (int i = 0; i < NGL; ++i) {
    if (derGl[i] || myWriteZero) { // by default store only non-zero derivatives
      if ((label[i] > 0 || myWriteZero) && label[i] <= myMaxLabel) { // and for valid labels
	++myBufferPos;
	myBufferFloat[myBufferPos] = derGl[i]; // global derivatives
	myBufferInt  [myBufferPos] = label[i]; // index of global parameter
      } else {
	std::cerr << "Mille::mille: Invalid label " << label[i] 
		  << " <= 0 or > " << myMaxLabel << std::endl; 
      }
    }
  }
}

//___________________________________________________________________________
/// Add special data to buffer.
/**
 * \param[in]    nSpecial   number of floats/ints
 * \param[in]    floatings  floats
 * \param[in]    integers   ints
 */
void Mille::special(int nSpecial, const float *floatings, const int *integers)
{
  if (nSpecial == 0) return;
  if (myBufferPos == -1) this->newSet(); // start, e.g. new track
  if (myHasSpecial) {
    std::cerr << "Mille::special: Special values already stored for this record."
	      << std::endl; 
    return;
  }
  if (!this->checkBufferSize(nSpecial, 0)) return;
  myHasSpecial = true; // after newSet() (Note: MILLSP sets to buffer position...)

  //  myBufferFloat[.]  | myBufferInt[.]
  // ------------------------------------
  //      0.0           |      0
  //  -float(nSpecial)  |      0
  //  The above indicates special data, following are nSpecial floating and nSpecial integer data.

  ++myBufferPos; // zero pair
  myBufferFloat[myBufferPos] = 0.;
  myBufferInt  [myBufferPos] = 0;

  ++myBufferPos; // nSpecial and zero
  myBufferFloat[myBufferPos] = -nSpecial; // automatic conversion to float
  myBufferInt  [myBufferPos] = 0;

  for (int i = 0; i < nSpecial; ++i) {
    ++myBufferPos;
    myBufferFloat[myBufferPos] = floatings[i];
    myBufferInt  [myBufferPos] = integers[i];
  }
}

//___________________________________________________________________________
/// Reset buffers, i.e. kill derivatives accumulated for current set.
void Mille::kill()
{
  myBufferPos = -1;
}

//___________________________________________________________________________
/// Write buffer (set of derivatives with same local parameters) to file.
void Mille::end()
{
  if (myBufferPos > 0) { // only if anything stored...
    const int numWordsToWrite = (myBufferPos + 1)*2;

    if (myAsBinary) {
      myOutFile.write(reinterpret_cast<const char*>(&numWordsToWrite), 
		      sizeof(numWordsToWrite));
      myOutFile.write(reinterpret_cast<char*>(myBufferFloat), 
		      (myBufferPos+1) * sizeof(myBufferFloat[0]));
      myOutFile.write(reinterpret_cast<char*>(myBufferInt), 
		      (myBufferPos+1) * sizeof(myBufferInt[0]));
    } else {
      myOutFile << numWordsToWrite << "\n";
      for (int i = 0; i < myBufferPos+1; ++i) {
	myOutFile << myBufferFloat[i] << " ";
      }
      myOutFile << "\n";
      
      for (int i = 0; i < myBufferPos+1; ++i) {
	myOutFile << myBufferInt[i] << " ";
      }
      myOutFile << "\n";
    }
  }
  myBufferPos = -1; // reset buffer for next set of derivatives
}

//___________________________________________________________________________
/// Initialize for new set of locals, e.g. new track.
void Mille::newSet()
{
  myBufferPos = 0;
  myHasSpecial = false;
  myBufferFloat[0] = 0.0;
  myBufferInt  [0] = 0;   // position 0 used as error counter
}

//___________________________________________________________________________
/// Enough space for next nLocal + nGlobal derivatives incl. measurement?
/**
 * \param[in]   nLocal  number of local derivatives
 * \param[in]   nGlobal number of global derivatives
 * \return      true if sufficient space available (else false)
 */
bool Mille::checkBufferSize(int nLocal, int nGlobal)
{
  if (myBufferPos + nLocal + nGlobal + 2 >= myBufferSize) {
    ++(myBufferInt[0]); // increase error count
    std::cerr << "Mille::checkBufferSize: Buffer too short (" 
	      << myBufferSize << "),"
	      << "\n need space for nLocal (" << nLocal<< ")"
	      << "/nGlobal (" << nGlobal << ") local/global derivatives, " 
	      << myBufferPos + 1 << " already stored!"
	      << std::endl;
    return false;
  } else {
    return true;
  }
}

void convert2mille_v2_ss(const char* inputFileName = "../Faser-Physics-015687-00410_3station_forward_kfalignment.root"){
  //data23
  Mille mille_file("mp2input.bin");
  int Nfile=1;

  for(int fileId=0;fileId<Nfile;fileId++){
    std::string InputFileName = inputFileName;
    std::cout << InputFileName << std::endl;
    TFile* f1=new TFile(InputFileName.c_str());
    TTree* t1=(TTree*)f1->Get("tree");
    bool dump6ndf_modules=false;

    bool dumplayers=true;
    bool dump6ndf_layers=true;
    bool dumpz_layers=false;
    bool dumpstations=false;
    bool dump6ndf_stations=true;
    bool use_sidebyside=true;

    double m_fitParam_x=0;
    double m_fitParam_y=0;
    double m_fitParam_pull_x=0;
    double m_fitParam_pull_y=0;
    double m_fitParam_chi2=0;
    double m_fitParam_ndf=0;
    double m_fitParam_nMeasurements=0;
    double m_fitParam_px=0;
    double m_fitParam_py=0;
    double m_fitParam_pz=0;
    double m_fitParam_charge=0;
    std::vector<double>* m_fitParam_align_global_derivation_y_x=0;
    std::vector<double>* m_fitParam_align_global_derivation_y_y=0;
    std::vector<double>* m_fitParam_align_global_derivation_y_z=0;
    std::vector<double>* m_fitParam_align_global_derivation_y_rx=0;
    std::vector<double>* m_fitParam_align_global_derivation_y_ry=0;
    std::vector<double>* m_fitParam_align_global_derivation_y_rz=0;
    std::vector<double>* m_fitParam_align_local_derivation_x_x=0;
    std::vector<double>* m_fitParam_align_local_derivation_x_y=0;
    std::vector<double>* m_fitParam_align_local_derivation_x_z=0;
    std::vector<double>* m_fitParam_align_local_derivation_x_rx=0;
    std::vector<double>* m_fitParam_align_local_derivation_x_ry=0;
    std::vector<double>* m_fitParam_align_local_derivation_x_rz=0;
    std::vector<double>* m_fitParam_align_local_residual_x=0;
    std::vector<double>* m_fitParam_align_local_measured_x=0;
    std::vector<double>* m_fitParam_align_local_measured_xe=0;
    std::vector<double>* m_fitParam_align_id=0;
    std::vector<double>* m_fitParam_align_local_derivation_x_par_x=0;
    std::vector<double>* m_fitParam_align_local_derivation_x_par_y=0;
    std::vector<double>* m_fitParam_align_local_derivation_x_par_theta=0;
    std::vector<double>* m_fitParam_align_local_derivation_x_par_phi=0;
    std::vector<double>* m_fitParam_align_local_derivation_x_par_qop=0;
    t1->SetBranchAddress("fitParam_x",&m_fitParam_x);
    t1->SetBranchAddress("fitParam_y",&m_fitParam_y);
    t1->SetBranchAddress("fitParam_chi2",&m_fitParam_chi2);
    t1->SetBranchAddress("fitParam_pz",&m_fitParam_pz);
    t1->SetBranchAddress("fitParam_px",&m_fitParam_px);
    t1->SetBranchAddress("fitParam_py",&m_fitParam_py);
    t1->SetBranchAddress("fitParam_charge",&m_fitParam_charge);
    t1->SetBranchAddress("fitParam_align_global_derivation_y_x",&m_fitParam_align_global_derivation_y_x);
    t1->SetBranchAddress("fitParam_align_global_derivation_y_y",&m_fitParam_align_global_derivation_y_y);
    t1->SetBranchAddress("fitParam_align_global_derivation_y_z",&m_fitParam_align_global_derivation_y_z);
    t1->SetBranchAddress("fitParam_align_global_derivation_y_rx",&m_fitParam_align_global_derivation_y_rx);
    t1->SetBranchAddress("fitParam_align_global_derivation_y_ry",&m_fitParam_align_global_derivation_y_ry);
    t1->SetBranchAddress("fitParam_align_global_derivation_y_rz",&m_fitParam_align_global_derivation_y_rz);
    t1->SetBranchAddress("fitParam_align_local_derivation_x_x",&m_fitParam_align_local_derivation_x_x);
    t1->SetBranchAddress("fitParam_align_local_derivation_x_y",&m_fitParam_align_local_derivation_x_y);
    t1->SetBranchAddress("fitParam_align_local_derivation_x_z",&m_fitParam_align_local_derivation_x_z);
    t1->SetBranchAddress("fitParam_align_local_derivation_x_rx",&m_fitParam_align_local_derivation_x_rx);
    t1->SetBranchAddress("fitParam_align_local_derivation_x_ry",&m_fitParam_align_local_derivation_x_ry);
    t1->SetBranchAddress("fitParam_align_local_derivation_x_rz",&m_fitParam_align_local_derivation_x_rz);
    t1->SetBranchAddress("fitParam_align_local_residual_x",&m_fitParam_align_local_residual_x);
    t1->SetBranchAddress("fitParam_align_local_measured_x",&m_fitParam_align_local_measured_x);
    t1->SetBranchAddress("fitParam_align_local_measured_xe",&m_fitParam_align_local_measured_xe);
    t1->SetBranchAddress("fitParam_align_id",&m_fitParam_align_id);
    t1->SetBranchAddress("fitParam_align_local_derivation_x_par_x",&m_fitParam_align_local_derivation_x_par_x);
    t1->SetBranchAddress("fitParam_align_local_derivation_x_par_y",&m_fitParam_align_local_derivation_x_par_y);
    t1->SetBranchAddress("fitParam_align_local_derivation_x_par_theta",&m_fitParam_align_local_derivation_x_par_theta);
    t1->SetBranchAddress("fitParam_align_local_derivation_x_par_phi",&m_fitParam_align_local_derivation_x_par_phi);
    t1->SetBranchAddress("fitParam_align_local_derivation_x_par_qop",&m_fitParam_align_local_derivation_x_par_qop);

    int nevt= t1->GetEntries();


    //loop over all the events
    std::vector<int> labels;
    std::vector<float> glo_der;
    std::vector<float> loc_der;
    float resi=0.;
    float resi_e=0.;
    bool diffside=false;

    int ioutput=0;
    int nhits[8]={0};
    for(int ievt = 0;ievt< nevt; ++ievt){
      t1->GetEntry(ievt);
  //std::cout<<"like "<<ievt<<" "<<m_fitParam_chi2/m_fitParam_ndf<<" "<<m_fitParam_pz<<" "<<m_fitParam_align_id->size()<<std::endl;
      if(m_fitParam_chi2>2000||m_fitParam_pz<100||m_fitParam_pz>5000||m_fitParam_align_id->size()<15)continue;
      //if(m_fitParam_chi2>500||m_fitParam_pz<100||m_fitParam_pz>5000||m_fitParam_align_id->size()<15)continue;
      ++ioutput;
  //    if(ioutput>1000)continue;
      for(int ihit = 0; ihit<m_fitParam_align_id->size();++ihit){
        labels.clear();
        glo_der.clear();
        loc_der.clear();
        if(fabs(m_fitParam_align_local_residual_x->at(ihit))>0.05)continue;
        if(m_fitParam_align_local_derivation_x_x->at(ihit)<-9000||m_fitParam_align_local_derivation_x_rz->at(ihit)<-9000||m_fitParam_align_global_derivation_y_x->at(ihit)<-9000||m_fitParam_align_global_derivation_y_y->at(ihit)<-9000||m_fitParam_align_global_derivation_y_z->at(ihit)<-9000||m_fitParam_align_global_derivation_y_rx->at(ihit)<-9000||m_fitParam_align_global_derivation_y_ry->at(ihit)<-9000||m_fitParam_align_global_derivation_y_rz->at(ihit)<-9000)continue;

        int moduleid = m_fitParam_align_id->at(ihit);

        diffside=false;
        //      std::cout<<"like moduleid "<<moduleid;
        if((moduleid%10==1)&&(!use_sidebyside))--moduleid;
        //      std::cout<<" "<<moduleid<<std::endl;
        moduleid+=1000;//station from 1 not 0
  //	int layerid = moduleid/100;
  //	if(moduleid/100==10){
  //	  if(nhits[moduleid%100/10]>1000)continue;
  //	  nhits[moduleid%100/10]+=1;
  //	}
  if(dump6ndf_modules){
    if(use_sidebyside){
      labels.push_back(moduleid*10+0+1);//millepede can not have label at 0
      labels.push_back(moduleid*10+1+1);
      glo_der.push_back(m_fitParam_align_local_derivation_x_x->at(ihit));
      glo_der.push_back(m_fitParam_align_local_derivation_x_y->at(ihit));
    }
    else{
      labels.push_back(moduleid*10+0+1);//millepede can not have label at 0
      glo_der.push_back(m_fitParam_align_local_derivation_x_x->at(ihit));
    }
    
    labels.push_back(moduleid*10+2+1);
    labels.push_back(moduleid*10+3+1);
    labels.push_back(moduleid*10+4+1);
    labels.push_back(moduleid*10+5+1);    
    glo_der.push_back(m_fitParam_align_local_derivation_x_z->at(ihit));
    glo_der.push_back(m_fitParam_align_local_derivation_x_rx->at(ihit));
    glo_der.push_back(m_fitParam_align_local_derivation_x_ry->at(ihit));
    glo_der.push_back(m_fitParam_align_local_derivation_x_rz->at(ihit));
  }
  else{
    labels.push_back(moduleid*10+0+1);//millepede can not have label at 0
    labels.push_back(((moduleid/10)*10)*10+1+1);
    glo_der.push_back(m_fitParam_align_local_derivation_x_x->at(ihit));
    glo_der.push_back(m_fitParam_align_local_derivation_x_rz->at(ihit));
  }
  if(dumplayers){
    int layerid = moduleid/100;
  //	std::cout<<"id "<<moduleid<<" "<<layerid<<std::endl;
    if(dump6ndf_layers){
      if(fabs(m_fitParam_align_global_derivation_y_rx->at(ihit))>2||fabs(m_fitParam_align_global_derivation_y_ry->at(ihit))>2)continue;
      labels.push_back(layerid*10+0+1);//millepede can not have label at 0
      labels.push_back(layerid*10+1+1);
      labels.push_back(layerid*10+2+1);
      labels.push_back(layerid*10+3+1);
      labels.push_back(layerid*10+4+1);
      glo_der.push_back(m_fitParam_align_global_derivation_y_x->at(ihit));
      glo_der.push_back(m_fitParam_align_global_derivation_y_y->at(ihit));
      if(dumpz_layers)
      {
        labels.push_back(layerid*10+5+1);
        glo_der.push_back(m_fitParam_align_global_derivation_y_z->at(ihit));
      }
      glo_der.push_back(m_fitParam_align_global_derivation_y_rx->at(ihit));
      glo_der.push_back(m_fitParam_align_global_derivation_y_ry->at(ihit));
      glo_der.push_back(m_fitParam_align_global_derivation_y_rz->at(ihit));
    }
    else{
      labels.push_back(layerid*10+0+1);//millepede can not have label at 0
      labels.push_back(layerid*10+1+1);
      glo_der.push_back(m_fitParam_align_global_derivation_y_y->at(ihit));
      glo_der.push_back(m_fitParam_align_global_derivation_y_rz->at(ihit));
    }
        }
        if(dumpstations){
    int stationid = moduleid/1000;
    if(dump6ndf_stations){
      labels.push_back(stationid*10+0+1);//millepede can not have label at 0
      labels.push_back(stationid*10+1+1);
      labels.push_back(stationid*10+2+1);
      labels.push_back(stationid*10+3+1);
      labels.push_back(stationid*10+4+1);
      labels.push_back(stationid*10+5+1);
      glo_der.push_back(m_fitParam_align_global_derivation_y_x->at(ihit));
      glo_der.push_back(m_fitParam_align_global_derivation_y_y->at(ihit));
      glo_der.push_back(m_fitParam_align_global_derivation_y_z->at(ihit));
      glo_der.push_back(m_fitParam_align_global_derivation_y_rx->at(ihit));
      glo_der.push_back(m_fitParam_align_global_derivation_y_ry->at(ihit));
      glo_der.push_back(m_fitParam_align_global_derivation_y_rz->at(ihit));
    }
    else{
      labels.push_back(stationid*10+0+1);//millepede can not have label at 0
      labels.push_back(stationid*10+1+1);
      glo_der.push_back(m_fitParam_align_global_derivation_y_y->at(ihit));
      glo_der.push_back(m_fitParam_align_global_derivation_y_rz->at(ihit));
    }
        }

        loc_der.push_back(m_fitParam_align_local_derivation_x_par_x->at(ihit));
        loc_der.push_back(m_fitParam_align_local_derivation_x_par_y->at(ihit));
        loc_der.push_back(m_fitParam_align_local_derivation_x_par_theta->at(ihit));
        loc_der.push_back(m_fitParam_align_local_derivation_x_par_phi->at(ihit));
        loc_der.push_back(m_fitParam_align_local_derivation_x_par_qop->at(ihit));
  //      std::cout<<"like "<<ievt<<" "<<ihit<<" "<<loc_der.size()<<std::endl;
        float* lcder = loc_der.data();
        float* glder = glo_der.data();
        int* label = labels.data();
        resi=m_fitParam_align_local_residual_x->at(ihit);
        resi_e=m_fitParam_align_local_measured_xe->at(ihit);
        mille_file.mille(loc_der.size(), lcder, glo_der.size(), glder, label, resi, resi_e);
      }
    mille_file.end();
  //    mille_file.flushTrack();
    }
  }
  mille_file.kill();


}
