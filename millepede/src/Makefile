CXX := g++

CXXFLAGS := `root-config --cflags`
CXXFLAGS += -I$(HOME)/work/Environments/cxx/argparse/install/include

LDFLAGS := `root-config --libs`

SOURCES = main.cc Mille.cc
OBJECTS = $(SOURCES:.cc=.o)
TARGET = convert

all: $(TARGET)
.PHONY : all

$(TARGET): $(OBJECTS)
	$(CXX) $(LDFLAGS) $^ -o $@

%.o: %.cc
	$(CXX) $(CXXFLAGS) -c $< -o $@

clean:
	rm -f $(OBJECTS) $(TARGET)
.PHONY : clean